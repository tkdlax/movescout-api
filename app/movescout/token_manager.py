from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.encryption import EncryptionService
from app.config import get_settings
from app.models.db import TokenCache, User
from app.movescout.client import MOVESCOUT_USER_AGENT


class TokenManager:
    def __init__(self, db: AsyncSession, encryption: EncryptionService) -> None:
        self.db = db
        self.encryption = encryption
        self.settings = get_settings()

    async def get_access_token(self, user: User, *, force_refresh: bool = False) -> str:
        if not force_refresh:
            cached = await self._get_cached_token(user.id)
            if cached:
                return cached

        return await self._authenticate_and_cache(user)

    async def invalidate_token(self, user: User) -> None:
        result = await self.db.execute(select(TokenCache).where(TokenCache.user_id == user.id))
        token = result.scalar_one_or_none()
        if token:
            await self.db.delete(token)
            await self.db.flush()

    async def _get_cached_token(self, user_id: Any) -> str | None:
        result = await self.db.execute(select(TokenCache).where(TokenCache.user_id == user_id))
        token = result.scalar_one_or_none()
        if not token:
            return None

        buffer = timedelta(seconds=self.settings.token_refresh_buffer_seconds)
        if token.expires_at > datetime.now(UTC) + buffer:
            return token.access_token
        return None

    async def _authenticate_and_cache(self, user: User) -> str:
        password = self.encryption.decrypt(user.movescout_password_enc)
        payload = {
            "userNameOrEmailAddress": user.movescout_username,
            "password": password,
            "rememberClient": True,
        }

        async with httpx.AsyncClient(
            base_url=self.settings.movescout_base_url,
            timeout=httpx.Timeout(30.0, connect=10.0),
        ) as client:
            try:
                response = await client.post(
                    "/api/TokenAuth/Authenticate",
                    json=payload,
                    headers={
                        "Content-Type": "application/json-patch+json",
                        "Accept": "text/plain",
                        "Origin": self.settings.movescout_origin,
                        "Referer": f"{self.settings.movescout_origin}/",
                        "User-Agent": MOVESCOUT_USER_AGENT,
                    },
                )
            except httpx.HTTPError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Failed to authenticate with MoveScout: {exc}",
                ) from exc

        if response.status_code != 200:
            body_preview = (response.text or "")[:300]
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    f"MoveScout authentication failed (HTTP {response.status_code}). "
                    f"Response: {body_preview or response.reason_phrase}"
                ),
            )

        data = response.json()
        if data.get("success") is False:
            err = data.get("error") or {}
            message = err.get("message") or err.get("details") or data.get("unAuthorizedRequest")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"MoveScout rejected login: {message or data}",
            )

        access_token = data.get("result", {}).get("accessToken")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"MoveScout authentication response missing access token: {data}",
            )

        expires_at = datetime.now(UTC) + timedelta(seconds=self.settings.token_expiry_seconds)
        result = await self.db.execute(select(TokenCache).where(TokenCache.user_id == user.id))
        token = result.scalar_one_or_none()

        if token:
            token.access_token = access_token
            token.expires_at = expires_at
        else:
            token = TokenCache(user_id=user.id, access_token=access_token, expires_at=expires_at)
            self.db.add(token)

        await self.db.flush()
        return access_token

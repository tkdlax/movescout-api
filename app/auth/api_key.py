import secrets

import bcrypt
from fastapi import Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db import User


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    return bcrypt.hashpw(api_key.encode(), bcrypt.gensalt()).decode()


def verify_api_key(api_key: str, api_key_hash: str) -> bool:
    return bcrypt.checkpw(api_key.encode(), api_key_hash.encode())


async def resolve_user_from_api_key(api_key: str | None, db: AsyncSession) -> User:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )

    result = await db.execute(select(User).where(User.is_active.is_(True)))
    users = result.scalars().all()

    for user in users:
        if verify_api_key(api_key, user.api_key_hash):
            return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
    )


async def get_current_user(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> User:
    return await resolve_user_from_api_key(x_api_key, db)


async def get_current_user_header_or_query(
    x_api_key_header: str | None = Header(default=None, alias="X-API-Key"),
    x_api_key_query: str | None = Query(default=None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Accept X-API-Key via header or query string (for URL-based file fetch e.g. Zapier)."""
    return await resolve_user_from_api_key(x_api_key_header or x_api_key_query, db)

#!/usr/bin/env python3
"""Update stored MoveScout username/password for an existing middleware user."""

import argparse
import asyncio
import sys
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.encryption import EncryptionService
from app.config import get_settings
from app.models.db import TokenCache, User


async def update_credentials(
    *,
    user_id: uuid.UUID | None,
    movescout_username_lookup: str | None,
    movescout_username: str | None,
    movescout_password: str,
) -> User:
    settings = get_settings()
    encryption = EncryptionService()

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        if user_id:
            result = await session.execute(select(User).where(User.id == user_id))
        else:
            result = await session.execute(
                select(User).where(User.movescout_username == movescout_username_lookup)
            )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        if movescout_username:
            user.movescout_username = movescout_username
        user.movescout_password_enc = encryption.encrypt(movescout_password)

        await session.execute(delete(TokenCache).where(TokenCache.user_id == user.id))
        await session.commit()

    await engine.dispose()
    return user


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Update MoveScout credentials for an existing API user (keeps same API key)"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--user-id", help="Middleware user UUID from create_user.py")
    group.add_argument(
        "--by-movescout-username",
        help="Find user by current MoveScout login (e.g. Q0103000048)",
    )
    parser.add_argument("--movescout-username", help="New MoveScout login (optional)")
    parser.add_argument("--movescout-password", required=True, help="New MoveScout password")
    args = parser.parse_args()

    user_id = uuid.UUID(args.user_id) if args.user_id else None

    try:
        user = asyncio.run(
            update_credentials(
                user_id=user_id,
                movescout_username_lookup=args.by_movescout_username,
                movescout_username=args.movescout_username,
                movescout_password=args.movescout_password,
            )
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Updated MoveScout credentials for: {user.name} (id={user.id})")
    print(f"MoveScout username: {user.movescout_username}")
    print("Cached MoveScout token cleared — next API call will re-authenticate.")
    print("Your X-API-Key is unchanged.")


if __name__ == "__main__":
    main()

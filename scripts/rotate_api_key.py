#!/usr/bin/env python3
"""Rotate a user's API key."""

import argparse
import asyncio
import sys
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.api_key import generate_api_key, hash_api_key
from app.config import get_settings
from app.models.db import User


async def rotate_key(user_id: uuid.UUID) -> str:
    settings = get_settings()
    api_key = generate_api_key()

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found")

        user.api_key_hash = hash_api_key(api_key)
        await session.commit()

    await engine.dispose()
    return api_key


def main() -> None:
    parser = argparse.ArgumentParser(description="Rotate API key for a user")
    parser.add_argument("--user-id", required=True, help="User UUID")
    args = parser.parse_args()

    try:
        user_id = uuid.UUID(args.user_id)
        api_key = asyncio.run(rotate_key(user_id))
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"API key rotated for user {user_id}")
    print(f"New API key (save this — shown once): {api_key}")


if __name__ == "__main__":
    main()

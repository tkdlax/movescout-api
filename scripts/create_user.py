#!/usr/bin/env python3
"""Create a middleware API user with MoveScout credentials."""

import argparse
import asyncio
import sys
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.api_key import generate_api_key, hash_api_key
from app.auth.encryption import EncryptionService
from app.config import get_settings
from app.models.db import User


async def create_user(
    name: str,
    movescout_username: str,
    movescout_password: str,
    sales_rep_name: str | None = None,
) -> tuple[User, str]:
    settings = get_settings()
    encryption = EncryptionService()
    api_key = generate_api_key()

    user = User(
        id=uuid.uuid4(),
        name=name,
        api_key_hash=hash_api_key(api_key),
        movescout_username=movescout_username,
        movescout_password_enc=encryption.encrypt(movescout_password),
        sales_rep_name=sales_rep_name,
    )

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        session.add(user)
        await session.commit()

    await engine.dispose()
    return user, api_key


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a MoveScout middleware API user")
    parser.add_argument("--name", required=True, help="Display name for the user")
    parser.add_argument("--movescout-username", required=True, help="MoveScout Pro username")
    parser.add_argument("--movescout-password", required=True, help="MoveScout Pro password")
    parser.add_argument("--sales-rep-name", help="Sales rep name for /queries/my-leads")
    args = parser.parse_args()

    try:
        user, api_key = asyncio.run(
            create_user(
                name=args.name,
                movescout_username=args.movescout_username,
                movescout_password=args.movescout_password,
                sales_rep_name=args.sales_rep_name,
            )
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"User created: {user.name} (id={user.id})")
    print(f"API key (save this — shown once): {api_key}")


if __name__ == "__main__":
    main()

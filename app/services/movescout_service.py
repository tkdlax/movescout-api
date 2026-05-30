from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.encryption import EncryptionService
from app.models.db import User
from app.movescout.client import MoveScoutClient, MoveScoutError
from app.movescout.token_manager import TokenManager


async def with_movescout_client[T](
    db: AsyncSession,
    user: User,
    callback: Callable[[MoveScoutClient], Awaitable[T]],
) -> T:
    encryption = EncryptionService()
    token_manager = TokenManager(db, encryption)

    async def run(force_refresh: bool = False) -> T:
        access_token = await token_manager.get_access_token(user, force_refresh=force_refresh)
        async with MoveScoutClient(access_token) as client:
            return await callback(client)

    try:
        return await run()
    except MoveScoutError as exc:
        if exc.status_code == 401:
            await token_manager.invalidate_token(user)
            return await run(force_refresh=True)
        raise

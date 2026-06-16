from typing import Any

from app.movescout.client import MoveScoutClient


async def get_all_list_of_values(client: MoveScoutClient) -> Any:
    return await client.request(
        "GET",
        "/api/services/app/ListOfValue/GetAllListofvalues",
    )

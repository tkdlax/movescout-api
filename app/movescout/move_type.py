from typing import Any

from app.movescout.client import MoveScoutClient


async def get_move_type(
    client: MoveScoutClient,
    *,
    origin_state: str,
    destination_state: str,
    origin_country: str = "US",
    destination_country: str = "US",
) -> Any:
    """Determine move type (Interstate/Intrastate/Local) based on origin/destination."""
    return await client.request(
        "GET",
        "/api/services/app/Lead/GetMoveType",
        params={
            "OriginState": origin_state,
            "DesinationState": destination_state,
            "OriginCountry": origin_country,
            "DesinationCountry": destination_country,
        },
    )

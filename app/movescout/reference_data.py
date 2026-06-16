from typing import Any

from app.movescout.client import MoveScoutClient


async def get_all_make_model_details(client: MoveScoutClient) -> Any:
    return await client.request(
        "GET",
        "/api/services/app/AutoMakeModel/GetAllMakeModelDetails",
    )


async def get_all_transit_guide_season_configuration(client: MoveScoutClient) -> Any:
    return await client.request(
        "GET",
        "/api/services/app/TransitGuideSeasonConfiguration/GetAllTransitGuideSeasonConfiguration",
    )


async def get_agent_list(client: MoveScoutClient) -> Any:
    return await client.request(
        "GET",
        "/api/services/app/Dropdown/GetAllAgentList",
    )

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


async def get_move_coordinator_list(client: MoveScoutClient, agency_id: int) -> Any:
    """Get move coordinators for an agency."""
    return await client.request(
        "GET",
        "/api/services/app/Dropdown/GetMoveCoordinatorListBasedOnAgencyId",
        params={"agencyId": agency_id},
    )


async def get_custom_tariff_list(client: MoveScoutClient, brand_id: int) -> Any:
    """Get custom tariff list for a brand."""
    return await client.request(
        "GET",
        "/api/services/app/CustomTariffAPIService/GetCTListForEstimate",
        params={"brandId": brand_id},
    )


async def get_lead_source_programs(
    client: MoveScoutClient,
    agency_id: int,
    *,
    page: int = 1,
    page_size: int = 100,
) -> Any:
    """Get paginated lead source programs for an agency."""
    from app.movescout.paging import movescout_skip_count

    return await client.request(
        "GET",
        "/api/services/app/LeadSourceProgram/GetPaginatedLeadSourceProgramByAgencyId",
        params={
            "AgencyId": agency_id,
            "MaxResultCount": page_size,
            "SkipCount": movescout_skip_count(page, page_size),
        },
    )

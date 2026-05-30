from typing import Any

from app.movescout.client import MoveScoutClient


async def get_primary_estimate(client: MoveScoutClient, lead_id: str) -> Any:
    return await client.request(
        "GET",
        "/api/services/app/Estimate/GetPrimaryEstimate",
        params={"id": lead_id},
    )


async def get_lead_estimate_by_id(
    client: MoveScoutClient,
    *,
    estimate_id: str,
    lead_id: str,
) -> Any:
    return await client.request(
        "GET",
        "/api/services/app/GetEstimate/GetLeadEstimateById",
        params={"estimateId": estimate_id, "leadId": lead_id},
    )


async def get_estimate_name(client: MoveScoutClient, estimate_id: str) -> Any:
    return await client.request(
        "GET",
        "/api/services/app/GetEstimate/GetEstimateName",
        params={"Id": estimate_id},
    )


async def get_brand_tariff_mapped_list(client: MoveScoutClient, estimate_id: str) -> Any:
    return await client.request(
        "GET",
        "/api/services/app/GetEstimate/GetBrandTariffMappedList",
        params={"estimateId": estimate_id},
    )


async def get_segments_for_lead_estimate(client: MoveScoutClient, estimate_id: str) -> Any:
    return await client.request(
        "GET",
        "/api/services/app/GetEstimate/GetSegmentsForLeadEstimate",
        params={"estimateId": estimate_id},
    )


async def get_estimate_accessorial_details(client: MoveScoutClient, estimate_id: str) -> Any:
    return await client.request(
        "GET",
        "/api/services/app/GetEstimate/GetEstimateAccessorialDetailsByEstimateId",
        params={"estimateId": estimate_id},
    )


async def get_estimate_pricing_total(client: MoveScoutClient, estimate_id: str) -> Any:
    return await client.request(
        "GET",
        "/api/services/app/GetEstimate/GetEstimatePricingTotalJsonResponse",
        params={"estimateId": estimate_id},
    )


async def get_estimate_auto_spot_details(client: MoveScoutClient, estimate_id: str) -> Any:
    return await client.request(
        "GET",
        "/api/services/app/GetEstimate/GetEstimateAutoSpotDetailsByEstimateId",
        params={"estimateId": estimate_id},
    )


async def get_estimate_customer_facing_notes(client: MoveScoutClient, estimate_id: str) -> Any:
    return await client.request(
        "GET",
        "/api/services/app/GetEstimate/GetEstimateCustomerFacingNotesByUserId",
        params={"estimateId": estimate_id},
    )

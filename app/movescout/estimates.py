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


async def get_estimate_tariff_by_effective_date(
    client: MoveScoutClient,
    *,
    estimate_id: str,
    tariff_id: int,
    tariff_name: str,
) -> Any:
    """Get tariff details for an estimate based on effective date."""
    return await client.request(
        "GET",
        "/api/services/app/GetEstimate/GetEstimateTariffByEffectiveDate",
        params={
            "estimateId": estimate_id,
            "tariffId": tariff_id,
            "tariffName": tariff_name,
        },
    )


async def update_lead_estimate(
    client: MoveScoutClient,
    estimate: dict[str, Any],
    *,
    tab_switch_flag: bool = False,
) -> Any:
    """Update an existing lead estimate (tariff, pricing fields, etc.)."""
    return await client.request(
        "PUT",
        "/api/services/app/Estimate/UpdateLeadEstimate",
        params={"tabSwitchFlag": str(tab_switch_flag).lower()},
        json=estimate,
    )


async def calculate_estimation_pricing(
    client: MoveScoutClient,
    pricing_request: dict[str, Any],
) -> Any:
    """Calculate pricing for an estimate."""
    return await client.request(
        "POST",
        "/api/services/app/Estimate/CalculateEstimationPricing",
        json=pricing_request,
    )

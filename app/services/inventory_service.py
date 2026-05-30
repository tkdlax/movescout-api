from typing import Any

from app.movescout.client import MoveScoutClient, MoveScoutError
from app.movescout.estimates import get_estimate_pricing_total, get_primary_estimate
from app.movescout.inventory import get_estimate_for_inventory_tab, get_estimate_summary
from app.movescout.responses import parse_abp_response
from app.services.inventory_transform import build_inventory_response


async def resolve_estimate_id(
    client: MoveScoutClient,
    lead_id: str,
    estimate_id: str | None,
) -> tuple[str, dict[str, Any] | None]:
    if estimate_id:
        return estimate_id, None

    response = await get_primary_estimate(client, lead_id)
    result = parse_abp_response(response, action="get primary estimate")
    if not result:
        raise MoveScoutError(
            f"No primary estimate found for lead {lead_id}",
            status_code=404,
            code="NO_PRIMARY_ESTIMATE",
        )

    if isinstance(result, dict):
        resolved = result.get("estimateId") or result.get("id")
        if resolved is not None:
            return str(resolved), result

    raise MoveScoutError(
        f"No primary estimate found for lead {lead_id}",
        status_code=404,
        code="NO_PRIMARY_ESTIMATE",
    )


async def fetch_inventory_by_lead(
    client: MoveScoutClient,
    lead_id: str,
    *,
    estimate_id: str | None = None,
    include_summary: bool = True,
    shipping_only: bool = False,
) -> dict[str, Any]:
    resolved_id, primary_meta = await resolve_estimate_id(client, lead_id, estimate_id)

    estimate_response = await get_estimate_for_inventory_tab(client, resolved_id)
    estimate_dto = parse_abp_response(estimate_response, action="get estimate for inventory tab")
    if not isinstance(estimate_dto, dict):
        estimate_dto = {}

    summary_result: dict[str, Any] | None = None
    if include_summary:
        summary_response = await get_estimate_summary(client, resolved_id)
        parsed = parse_abp_response(summary_response, action="get estimate summary")
        if isinstance(parsed, dict):
            summary_result = parsed

    return build_inventory_response(
        lead_id=lead_id,
        estimate_dto=estimate_dto,
        primary_meta=primary_meta,
        summary_result=summary_result,
        shipping_only=shipping_only,
    )


async def fetch_pricing_by_lead(
    client: MoveScoutClient,
    lead_id: str,
    *,
    estimate_id: str | None = None,
) -> dict[str, Any]:
    """Resolve primary estimate (unless estimateId given) and return pricing totals JSON."""
    resolved_id, primary_meta = await resolve_estimate_id(client, lead_id, estimate_id)

    pricing_response = await get_estimate_pricing_total(client, resolved_id)
    pricing = parse_abp_response(pricing_response, action="get estimate pricing")

    response: dict[str, Any] = {
        "leadId": int(lead_id) if str(lead_id).isdigit() else lead_id,
        "estimateId": int(resolved_id) if str(resolved_id).isdigit() else resolved_id,
    }
    if primary_meta:
        if primary_meta.get("estimateName"):
            response["estimateName"] = primary_meta["estimateName"]
        response["isPrimaryEstimate"] = True
    elif estimate_id:
        response["isPrimaryEstimate"] = False

    if isinstance(pricing, dict):
        response.update(pricing)
    else:
        response["result"] = pricing

    return response

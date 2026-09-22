"""STS (Registration) read functions for MoveScout Pro.

P9 capture (2026-09-22): Read-only access to STS registration data.
No write APIs were captured; do not invent Register/STS mutate endpoints.
"""

from typing import Any

from app.movescout.client import MoveScoutClient


async def get_all_agent_sales_rep_by_lead_id(
    client: MoveScoutClient,
    lead_id: int | str,
) -> Any:
    """GET /api/services/app/LeadEstimateSTSRegDetails/GetAllAgentSalesRepByLeadId

    P9 capture: Returns result: [] for lead 1674404 (no sales reps configured).
    """
    return await client.request(
        "GET",
        "/api/services/app/LeadEstimateSTSRegDetails/GetAllAgentSalesRepByLeadId",
        params={"leadId": lead_id},
    )


async def get_lead_estimate_sts_reg_details_by_id(
    client: MoveScoutClient,
    lead_id: int | str,
) -> Any:
    """GET /api/services/app/LeadEstimateSTSRegDetails/GetLeadEstimateSTSRegDetailsById

    P9 capture: May return 500 ABP error "Please select originating agent on lead."
    when lead lacks originating agent configuration. The middleware surfaces this
    as a normal upstream error.
    """
    return await client.request(
        "GET",
        "/api/services/app/LeadEstimateSTSRegDetails/GetLeadEstimateSTSRegDetailsById",
        params={"Id": lead_id},
    )

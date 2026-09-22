"""MoveScout MCP tool definitions.

Each tool maps 1:1 to a middleware REST route.
"""

from typing import Any

import httpx
from mcp.types import Tool


def _tool(name: str, description: str, properties: dict, required: list[str] | None = None) -> Tool:
    """Helper to create a Tool with input schema."""
    return Tool(
        name=name,
        description=description,
        inputSchema={
            "type": "object",
            "properties": properties,
            "required": required or [],
        },
    )


TOOLS: list[Tool] = [
    _tool(
        "movescout_leads_list",
        (
            "List leads with pagination and optional filters via POST Lead/GetAllLead. "
            "P11 capture evidence: supports filters[] array for per-column filtering. "
            "LIVE-PROVEN FILTER FIELDS: "
            "CONTAINS operator: id (Record Id), leadCustomerDetail.lastName, leadCustomerDetail.firstName, "
            "leadCustomerDetail.primaryEmailAddress, leadcustomerdetail.homephone (exact lowercase wire spelling), "
            "leadLMP.lmpId, agencyCode, registrationNumber, salesRepName, createdUserName. "
            "EQ operator: appointmentTypeId, dispositionId, moveTypeId, mobileSyncFlag (true), isQualifiedLead (true), "
            "estimateTotal (numeric), fundedId, dwellingTypeId, leadNonConforming.nonConformingFlag (true), "
            "leadMoSys.canadaGovMove (true). "
            "DATE PRESETS (eq with {id, value} objects): assignedDate, creationTime, leadMoveDate.loadFromDate, "
            "primaryLeadEstimate.effectiveDate, validThruDate, lastModificationTime. "
            "Previous Month preset = {id: 5, value: 30}. "
            "logic: '' (empty) for baseline, 'and' when filters are active. "
            "Each filter object: {field, operator, value, condition: 'and', date: HTTP date}. "
            "DO NOT INVENT encodings for: Booking Agent Name, Coordinator, Created Source, Mobile Sync Status, "
            "Lost Reason, Load To Date, Expected Delivery Date, Appt Created Date, Modified By, Transfer Type, Local Carrier."
        ),
        {
            "page": {"type": "integer", "description": "Page number (1-indexed)", "default": 1},
            "maxResultSize": {"type": "integer", "description": "Results per page", "default": 500},
            "defaultFilter": {"type": "integer", "description": "Lead filter (0-12)", "default": 3},
            "sortField": {"type": "string", "description": "Field to sort by"},
            "sortDir": {"type": "string", "description": "Sort direction (asc/desc)", "default": "desc"},
            "filters": {
                "type": "array",
                "description": (
                    "Array of filter objects for per-column filtering. Each filter: "
                    "{field: string, operator: 'contains'|'eq', value: string|object, condition: 'and'}. "
                    "CONTAINS fields: id, leadCustomerDetail.lastName/firstName/primaryEmailAddress, "
                    "leadcustomerdetail.homephone (exact lowercase), leadLMP.lmpId, agencyCode, registrationNumber, "
                    "salesRepName, createdUserName. "
                    "EQ fields: appointmentTypeId, dispositionId, moveTypeId, mobileSyncFlag, isQualifiedLead, "
                    "estimateTotal, fundedId, dwellingTypeId, leadNonConforming.nonConformingFlag, leadMoSys.canadaGovMove. "
                    "DATE PRESET fields (eq with {id, value}): assignedDate, creationTime, leadMoveDate.loadFromDate, "
                    "primaryLeadEstimate.effectiveDate, validThruDate, lastModificationTime. "
                    "Previous Month = {id: 5, value: 30}."
                ),
                "items": {"type": "object"},
            },
            "logic": {
                "type": "string",
                "description": "Filter logic: '' (empty) for no filters, 'and' when filters are active",
                "default": "",
            },
        },
    ),
    _tool(
        "movescout_leads_get",
        "Get a single lead by ID",
        {"leadId": {"type": "string", "description": "Lead ID"}},
        ["leadId"],
    ),
    _tool(
        "movescout_leads_create",
        "Create a new lead",
        {"lead": {"type": "object", "description": "Lead data"}},
        ["lead"],
    ),
    _tool(
        "movescout_leads_update",
        "Update an existing lead",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "lead": {"type": "object", "description": "Lead data to update"},
        },
        ["leadId", "lead"],
    ),
    _tool(
        "movescout_leads_move_type",
        "Get move type (Interstate/Intrastate/Local) based on origin/destination",
        {
            "originState": {"type": "string", "description": "Origin state code"},
            "destinationState": {"type": "string", "description": "Destination state code"},
            "originCountry": {"type": "string", "description": "Origin country code", "default": "US"},
            "destinationCountry": {"type": "string", "description": "Destination country code", "default": "US"},
        },
        ["originState", "destinationState"],
    ),
    _tool(
        "movescout_activities_list",
        "List activities for a lead",
        {"leadId": {"type": "string", "description": "Lead ID"}},
        ["leadId"],
    ),
    _tool(
        "movescout_activities_get",
        "Get a single activity by ID",
        {"activityId": {"type": "string", "description": "Activity ID"}},
        ["activityId"],
    ),
    _tool(
        "movescout_activities_create",
        (
            "Create or update an activity for a lead via POST /api/services/app/Activity/CreateOrUpdateActivity?triggerWF=true. "
            "Supports Survey (1), Task (2), Event (3), and Reminder (4) activity types. "
            "P7 capture evidence: Task create uses activityType=2, activityStatus=2 (Assigned), no id field. "
            "Task cancel/update includes id field with activityStatus=3 (Cancelled). "
            "Activity statuses: 2=Assigned, 3=Cancelled, 4=Completed. "
            "Key fields: activityName, description, activityType, activityStatus, activityStart, activityEnd, "
            "activityAssigneeId, leadId, reminderType (1=standard), locationType (2=Residential), activityLocation. "
            "For updates, include the activity id; for creates, omit it. "
            "Survey appointments (activityType=1) are handled separately via the appointments endpoint."
        ),
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "activity": {
                "type": "object",
                "description": (
                    "Activity data. Key fields: activityName, description (HTML), activityType (1=Survey, 2=Task, 3=Event, 4=Reminder), "
                    "activityStatus (2=Assigned, 3=Cancelled, 4=Completed), activityStart, activityEnd (ISO 8601), "
                    "activityAssigneeId, reminderType, locationType, activityLocation. For updates include id field."
                ),
            },
        },
        ["leadId", "activity"],
    ),
    _tool(
        "movescout_estimates_list",
        "List estimates for a lead",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "page": {"type": "integer", "description": "Page number", "default": 1},
            "maxResultSize": {"type": "integer", "description": "Results per page", "default": 15},
        },
        ["leadId"],
    ),
    _tool(
        "movescout_estimates_get_primary",
        "Get the primary estimate for a lead",
        {"leadId": {"type": "string", "description": "Lead ID"}},
        ["leadId"],
    ),
    _tool(
        "movescout_estimates_get",
        "Get estimate details",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
        },
        ["leadId", "estimateId"],
    ),
    _tool(
        "movescout_estimates_create",
        "Create an estimate (with or without inventory)",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimate": {"type": "object", "description": "Estimate data"},
        },
        ["leadId", "estimate"],
    ),
    _tool(
        "movescout_estimates_update",
        (
            "Update an existing estimate via PUT /api/services/app/Estimate/UpdateLeadEstimate. "
            "The estimate body is a full estimate DTO. "
            "TARIFF: pricingTariffId is authoritative (658=TPG, 659=Allied Express, 660=TPG GRR, 667=UAS). "
            "LEVEL: pricingLevelId/pricingLevel (e.g., 718/'Level 4') DOES affect pricing. "
            "CLASS: allianceDto.priceClassId can be set but persistence into calculate is NOT confirmed—"
            "subsequent CalculateEstimationPricing still shows priceClassId=null. Do not claim class saves work. "
            "ECP: valuationTypeId/tariffValuationType/valuationAmount/valuationBracketId for deductibles. "
            "ACCESSORIALS (P8): estimateAccessorialDto contains accessorial fields: "
            "exclusiveUseOfVehicleCubicFtFlag (bool), exclusiveUseOfVehicleCubicFeet (int, cubic feet), "
            "expeditedService (bool), spaceReservationCubicFtFlag, spaceReservationCubicFeet, "
            "shuttleServiceOnOffOrigin/Destination, extraLaborOriginApply, waitingTimeOriginApply, etc. "
            "Query param tabSwitchFlag (default false) controls validation behavior."
        ),
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
            "estimate": {
                "type": "object",
                "description": (
                    "Full estimate DTO. Key fields: pricingTariffId (authoritative), pricingLevelId, "
                    "pricingLevel, valuationTypeId, tariffValuationType, valuationAmount, valuationBracketId, "
                    "allianceDto (priceClassId persistence unconfirmed), segmentDto, estimateSITDto, "
                    "estimateAccessorialDto (exclusiveUseOfVehicleCubicFtFlag, exclusiveUseOfVehicleCubicFeet, "
                    "expeditedService, shuttle/labor/waiting fields)."
                ),
            },
            "tabSwitchFlag": {
                "type": "boolean",
                "description": "Validation flag (default false)",
                "default": False,
            },
        },
        ["leadId", "estimateId", "estimate"],
    ),
    _tool(
        "movescout_estimates_rooms_list",
        "List rooms for an estimate",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
        },
        ["leadId", "estimateId"],
    ),
    _tool(
        "movescout_estimates_rooms_create",
        "Create a room for an estimate",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
            "room": {"type": "object", "description": "Room data"},
        },
        ["leadId", "estimateId", "room"],
    ),
    _tool(
        "movescout_estimates_articles_catalog",
        "Get article catalog for a room",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
            "roomId": {"type": "integer", "description": "Room ID"},
        },
        ["leadId", "estimateId", "roomId"],
    ),
    _tool(
        "movescout_estimates_articles_create",
        "Create a custom article for a room",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
            "roomId": {"type": "integer", "description": "Room ID"},
            "article": {"type": "object", "description": "Article data"},
        },
        ["leadId", "estimateId", "roomId", "article"],
    ),
    _tool(
        "movescout_estimates_inventory_lines_update",
        (
            "Update inventory line items via POST CreateOrUpdateArticleForListInventory. "
            "The lines array is the FULL inventory state for the estimate. "
            "For stock article add: set articleId (catalog ID), articleCode, roomId, shippingQty, "
            "isCustomArticle=false, isQtyChange=true. "
            "For qty/weight/cube changes: update the existing line with new values and isQtyChange=true. "
            "NOTE: Under-minimum inventory produces flat pricing regardless of changes. "
            "After update, call calculate-pricing to see new totals, then inventory/save to commit."
        ),
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
            "lines": {
                "type": "array",
                "description": (
                    "Full inventory line items array. Key fields per item: articleId, articleCode, "
                    "roomId, shippingQty, weight, cube, isCustomArticle, isQtyChange"
                ),
            },
        },
        ["leadId", "estimateId", "lines"],
    ),
    _tool(
        "movescout_estimates_inventory_article_update",
        (
            "Update a single inventory article in place via POST CreateOrUpdateArticleForInventory. "
            "This is for in-place edits on existing articles (qty bump, weight/cube change). "
            "Unlike the bulk lines endpoint, this takes a single article object. "
            "P3-F evidence: Used for qty 2→3 bump on articleId 870, weight/cube 70/10→77/11 changes. "
            "Key fields: estimatesId, articleId (required), shippingQty, weight, cube, isQtyChange=true, "
            "roomId, segmentId, plus article flags (domestic, canada, maX3, maX4, grr, tariff400N, "
            "tarriff104G, uasFlg, local, international, carton, bulky, etc.). "
            "NOTE: Under-minimum inventory produces flat pricing. "
            "Response includes full Calculate pricing result (totalEstimationPriceNet in pricingResponseJson)."
        ),
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
            "article": {
                "type": "object",
                "description": (
                    "Single article object with full inventory line fields. Required: articleId, "
                    "shippingQty, roomId, segmentId. For edits set isQtyChange=true. "
                    "Include weight, cube, and all tariff/flag fields from existing article."
                ),
            },
        },
        ["leadId", "estimateId", "article"],
    ),
    _tool(
        "movescout_estimates_inventory_save",
        "Save/commit inventory changes",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
            "density": {"type": "integer", "description": "Density value", "default": 7},
        },
        ["leadId", "estimateId"],
    ),
    _tool(
        "movescout_estimates_pricing_get",
        "Get pricing totals for an estimate",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
        },
        ["leadId", "estimateId"],
    ),
    _tool(
        "movescout_estimates_accessorials_get",
        (
            "Get accessorial details for an estimate via GET GetEstimateAccessorialDetailsByEstimateId. "
            "P8 capture evidence: Returns estimateAccessorialDto with fields for exclusive use of vehicle, "
            "expedited service, shuttle service, extra labor, waiting time, stairs, elevator, excessive distance, "
            "piano handling, appliance servicing, rigging, assembling, and more. "
            "Key fields: exclusiveUseOfVehicleCubicFtFlag (bool), exclusiveUseOfVehicleCubicFeet (number), "
            "expeditedService (bool), spaceReservationCubicFtFlag, shuttleServiceOnOffOrigin/Destination, "
            "extraLaborOriginApply, waitingTimeOriginApply, isOriginStairsApply, isOriginElevatorApply, etc."
        ),
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
        },
        ["leadId", "estimateId"],
    ),
    _tool(
        "movescout_estimates_alliance_get",
        (
            "Get alliance pricing data for an estimate via GET Alliance/GetAllianceByLeadEstimateId. "
            "P8 capture evidence: Returns alliance quote data including priceClassId, total, quoteId, "
            "quoteGuid, allianceEstimateNumber, originServiceDate, destinationServiceDate, quoteRequestDate. "
            "Note: priceClassId may be null if no alliance price class is selected."
        ),
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
        },
        ["leadId", "estimateId"],
    ),
    _tool(
        "movescout_estimates_auto_spot_get",
        (
            "Get auto spot (vehicle transport) details for an estimate via GET GetEstimateAutoSpotDetailsByEstimateId. "
            "P8 capture evidence: Returns estimateAutoSpotDto with isContractAuto flag, contractChargeAmount, comment, "
            "estimateAutoSpotVehicles array (vehicle details), and estimateAutoSpotPriceOptions array (pricing options). "
            "NOTE: P8 capture showed empty vehicle/price-option arrays—Add Auto Spot was disabled in UI. "
            "Auto Spot write API was NOT captured; do not invent write operations from this read."
        ),
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
        },
        ["leadId", "estimateId"],
    ),
    _tool(
        "movescout_estimates_pricing_calculate",
        (
            "Calculate pricing via POST /api/services/app/Estimate/CalculateEstimationPricing. "
            "The pricingRequest is the full estimate DTO with pricing-relevant fields. "
            "TARIFFS: pricingTariffId is authoritative—658=TPG (baseline), 659=Allied Express (+2.9%), "
            "660=TPG GRR (same as TPG), 667=UAS (+84.5%). 664=Local/Intrastate is UI-blocked with "
            "'Are you sure?' confirmation that clears estimate details; no calculate observed. "
            "Legacy pricingTariff string may lag the numeric ID. "
            "LEVELS: pricingLevelId/pricingLevel DO affect totals—715=Level 1, 718=Level 4, "
            "724=Level 10, 804=Level 20 (Level 1→20: +79.7%). P3-G confirms 715/724 with TPG tariff. "
            "CLASSES: allianceDto.priceClassId is always null in calculate DTO—UI class selection "
            "(e.g., Bailey's Consumer 2019 priceClassId=3976) does NOT affect calculate results. "
            "DATES: loadFrom/deliverTo may be absent or null—API still returns HTTP 200. "
            "ECP: valuationTypeId/tariffValuationType (683='ECP - $0 Ded', 684='$250 Ded', 685='$500 Ded'). "
            "ACCESSORIALS (P8): estimateAccessorialDto nested in request controls accessorial pricing: "
            "exclusiveUseOfVehicleCubicFtFlag (bool), exclusiveUseOfVehicleCubicFeet (int), expeditedService (bool), "
            "and other shuttle/labor/waiting time fields. P8 capture: enabling exclusive use (100 cu ft) "
            "did not change Grand Total ($2,771.90) for the test estimate. "
            "UNDER-MIN: Inventory under minimum produces flat pricing regardless of qty/weight/cube changes. "
            "TYPO: Response contains 'totalEstimatinPriceNet' (missing 'o'); SMF at transportationSubItemCharges.totalSMFPriceNet."
        ),
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
            "pricingRequest": {
                "type": "object",
                "description": (
                    "Full estimate DTO. Key pricing fields: pricingTariffId (authoritative—658/659/660/667), "
                    "pricingLevelId (715/718/724/804), pricingLevel, loadFrom, deliverTo, valuationTypeId, "
                    "tariffValuationType, valuationAmount, valuationBracketId, peakOrNonPeak (false=non-peak), "
                    "estimateAccessorialDto (exclusiveUseOfVehicleCubicFtFlag, exclusiveUseOfVehicleCubicFeet, expeditedService)"
                ),
            },
        },
        ["leadId", "estimateId", "pricingRequest"],
    ),
    _tool(
        "movescout_estimates_tariff_effective",
        "Get tariff details by effective date",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
            "tariffId": {"type": "integer", "description": "Tariff ID"},
            "tariffName": {"type": "string", "description": "Tariff name"},
        },
        ["leadId", "estimateId", "tariffId", "tariffName"],
    ),
    _tool(
        "movescout_reference_lov",
        "Get list of values (enums)",
        {"refresh": {"type": "boolean", "description": "Force refresh cache", "default": False}},
    ),
    _tool(
        "movescout_reference_service_items",
        "Get alliance service items",
        {"refresh": {"type": "boolean", "description": "Force refresh cache", "default": False}},
    ),
    _tool(
        "movescout_reference_price_classes",
        "Get price classes for a booker",
        {"bookerId": {"type": "string", "description": "Booker/agency ID"}},
        ["bookerId"],
    ),
    _tool(
        "movescout_reference_move_coordinators",
        "Get move coordinators for an agency",
        {"agencyId": {"type": "integer", "description": "Agency ID"}},
        ["agencyId"],
    ),
    _tool(
        "movescout_reference_custom_tariffs",
        "Get custom tariffs for a brand",
        {"brandId": {"type": "integer", "description": "Brand ID"}},
        ["brandId"],
    ),
    _tool(
        "movescout_reference_lead_source_programs",
        "Get lead source programs for an agency",
        {
            "agencyId": {"type": "integer", "description": "Agency ID"},
            "page": {"type": "integer", "description": "Page number", "default": 1},
            "maxResultSize": {"type": "integer", "description": "Results per page", "default": 100},
        },
        ["agencyId"],
    ),
    _tool(
        "movescout_reference_agents",
        "Get all Sirva network agents",
        {"refresh": {"type": "boolean", "description": "Force refresh cache", "default": False}},
    ),
    _tool(
        "movescout_inventory_get",
        "Get room-grouped inventory for a lead (hero endpoint)",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Optional estimate ID"},
            "includeSummary": {"type": "boolean", "description": "Include summary", "default": True},
            "shippingOnly": {"type": "boolean", "description": "Shipping items only", "default": False},
        },
        ["leadId"],
    ),
    _tool(
        "movescout_estimates_segments_list",
        "Get segments for an estimate",
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
        },
        ["leadId", "estimateId"],
    ),
    _tool(
        "movescout_estimates_segments_update",
        (
            "Create or update segments via POST /api/services/app/Inventory/CreateOrUpdateSegments. "
            "P6 capture evidence: Body is { leadId, segmentDto: [...], id: estimateId }. "
            "Each segmentDto item: estimatesId, pickupAddressId, deliveryAddressId, pickupAddressName, "
            "deliveryAddressName, cube, weight, modeId (192=Road), name, tenantId, pickupStopName, "
            "deliveryStopName, id (existing segment ID or 0 for new). "
            "Creating a new segment: set id: 0 in segmentDto; the response returns the assigned ID."
        ),
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
            "segments": {
                "type": "object",
                "description": (
                    "Segments payload: { segmentDto: [...] }. leadId and id are injected from path params."
                ),
            },
        },
        ["leadId", "estimateId", "segments"],
    ),
    _tool(
        "movescout_estimates_extra_stops_save",
        (
            "Save extra pickup/delivery stops via POST /api/services/app/Inventory/SaveExtraPickUpAndDeliveriesForSegments. "
            "P6 capture evidence: Body is an array of stop address objects. Include ALL stops (main + extra). "
            "Each stop: leadId, estimatesId, streetAddr1, streetAddr2, zip, city, state, county, country, "
            "contactFirstName, contactNumber, emailAddress, addressType (1=pickup, 2=delivery), stopName, "
            "sequenceNumber, isMainPickup, isMainDelivery, id (address ID or 0 for new). "
            "The response returns assigned address IDs for new stops."
        ),
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
            "stops": {
                "type": "array",
                "description": (
                    "Array of stop address objects. leadId and estimatesId are injected from path params if missing."
                ),
            },
        },
        ["leadId", "estimateId", "stops"],
    ),
    _tool(
        "movescout_sts_agent_sales_reps",
        (
            "Get STS agent sales reps for a lead via GET LeadEstimateSTSRegDetails/GetAllAgentSalesRepByLeadId. "
            "P9 capture evidence: Returns array of agent sales rep records (may be empty). "
            "No STS write APIs were captured; this is read-only."
        ),
        {"leadId": {"type": "string", "description": "Lead ID"}},
        ["leadId"],
    ),
    _tool(
        "movescout_sts_reg_details",
        (
            "Get STS registration details for a lead via GET LeadEstimateSTSRegDetails/GetLeadEstimateSTSRegDetailsById. "
            "P9 capture evidence: May return 500 ABP error 'Please select originating agent on lead.' "
            "when lead lacks originating agent configuration. The error is surfaced as a normal upstream error. "
            "No STS write APIs were captured; this is read-only."
        ),
        {"leadId": {"type": "string", "description": "Lead ID"}},
        ["leadId"],
    ),
    _tool(
        "movescout_estimates_reports_list",
        (
            "Get reports/documents for an estimate via GET Report/GetAllEstimateReportsByEstimateId. "
            "P10 observation: Returns list of estimate reports/documents. "
            "UI shows 'Documents not found' when empty. No upload control was captured; this is read-only."
        ),
        {
            "leadId": {"type": "string", "description": "Lead ID"},
            "estimateId": {"type": "string", "description": "Estimate ID"},
        },
        ["leadId", "estimateId"],
    ),
    _tool(
        "movescout_reference_email_templates",
        (
            "Get email templates for an agency via GET CustomerEmailTemplate/GetEmailTemplatesByAgencyId. "
            "P10 observation: Returns list of customer email templates for the agency. "
            "No email send API was captured (modal was canceled); this is read-only."
        ),
        {"agencyId": {"type": "integer", "description": "Agency ID"}},
        ["agencyId"],
    ),
]


async def execute_tool(client: httpx.AsyncClient, name: str, arguments: dict[str, Any]) -> Any:
    """Execute an MCP tool by calling the appropriate middleware endpoint."""
    
    async def _leads_list(a: dict[str, Any]) -> httpx.Response:
        filters = a.get("filters")
        if filters:
            return await client.post("/leads/query", json={
                "page": a.get("page", 1),
                "maxResultSize": a.get("maxResultSize", 500),
                "defaultFilter": a.get("defaultFilter", 3),
                "sortField": a.get("sortField"),
                "sortDir": a.get("sortDir", "desc"),
                "filters": filters,
                "logic": a.get("logic", "and"),
            })
        return await client.get("/leads", params={
            "page": a.get("page", 1),
            "maxResultSize": a.get("maxResultSize", 500),
            "defaultFilter": a.get("defaultFilter", 3),
            "sortField": a.get("sortField"),
            "sortDir": a.get("sortDir", "desc"),
        })

    routes = {
        "movescout_leads_list": _leads_list,
        "movescout_leads_get": lambda a: client.get(f"/leads/{a['leadId']}"),
        "movescout_leads_create": lambda a: client.post("/leads", json=a["lead"]),
        "movescout_leads_update": lambda a: client.put(f"/leads/{a['leadId']}", json=a["lead"]),
        "movescout_leads_move_type": lambda a: client.get("/leads/move-type", params={
            "originState": a["originState"],
            "destinationState": a["destinationState"],
            "originCountry": a.get("originCountry", "US"),
            "destinationCountry": a.get("destinationCountry", "US"),
        }),
        "movescout_activities_list": lambda a: client.get(f"/leads/{a['leadId']}/appointments"),
        "movescout_activities_get": lambda a: client.get(f"/activities/{a['activityId']}"),
        "movescout_activities_create": lambda a: client.post(
            f"/leads/{a['leadId']}/activities", json=a["activity"]
        ),
        "movescout_estimates_list": lambda a: client.get(
            f"/leads/{a['leadId']}/estimates",
            params={"page": a.get("page", 1), "maxResultSize": a.get("maxResultSize", 15)},
        ),
        "movescout_estimates_get_primary": lambda a: client.get(
            f"/leads/{a['leadId']}/estimates/primary"
        ),
        "movescout_estimates_get": lambda a: client.get(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}"
        ),
        "movescout_estimates_create": lambda a: client.post(
            f"/leads/{a['leadId']}/estimates", json=a["estimate"]
        ),
        "movescout_estimates_update": lambda a: client.put(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}",
            params={"tabSwitchFlag": a.get("tabSwitchFlag", False)},
            json=a["estimate"],
        ),
        "movescout_estimates_rooms_list": lambda a: client.get(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/rooms"
        ),
        "movescout_estimates_rooms_create": lambda a: client.post(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/rooms", json=a["room"]
        ),
        "movescout_estimates_articles_catalog": lambda a: client.get(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/rooms/{a['roomId']}/articles"
        ),
        "movescout_estimates_articles_create": lambda a: client.post(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/rooms/{a['roomId']}/articles",
            json=a["article"],
        ),
        "movescout_estimates_inventory_lines_update": lambda a: client.put(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/inventory/lines",
            json=a["lines"],
        ),
        "movescout_estimates_inventory_article_update": lambda a: client.post(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/inventory/article",
            json=a["article"],
        ),
        "movescout_estimates_inventory_save": lambda a: client.post(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/inventory/save",
            params={"density": a.get("density", 7)},
        ),
        "movescout_estimates_pricing_get": lambda a: client.get(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/pricing"
        ),
        "movescout_estimates_accessorials_get": lambda a: client.get(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/accessorials"
        ),
        "movescout_estimates_alliance_get": lambda a: client.get(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/alliance"
        ),
        "movescout_estimates_auto_spot_get": lambda a: client.get(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/auto-spot"
        ),
        "movescout_estimates_pricing_calculate": lambda a: client.post(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/calculate-pricing",
            json=a["pricingRequest"],
        ),
        "movescout_estimates_tariff_effective": lambda a: client.get(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/tariff-effective",
            params={"tariffId": a["tariffId"], "tariffName": a["tariffName"]},
        ),
        "movescout_reference_lov": lambda a: client.get(
            "/lov", params={"refresh": a.get("refresh", False)}
        ),
        "movescout_reference_service_items": lambda a: client.get(
            "/reference/service-items", params={"refresh": a.get("refresh", False)}
        ),
        "movescout_reference_price_classes": lambda a: client.get(
            "/reference/price-classes", params={"bookerId": a["bookerId"]}
        ),
        "movescout_reference_move_coordinators": lambda a: client.get(
            "/reference/move-coordinators", params={"agencyId": a["agencyId"]}
        ),
        "movescout_reference_custom_tariffs": lambda a: client.get(
            "/reference/custom-tariffs", params={"brandId": a["brandId"]}
        ),
        "movescout_reference_lead_source_programs": lambda a: client.get(
            "/reference/lead-source-programs",
            params={
                "agencyId": a["agencyId"],
                "page": a.get("page", 1),
                "maxResultSize": a.get("maxResultSize", 100),
            },
        ),
        "movescout_reference_agents": lambda a: client.get(
            "/reference/agents", params={"refresh": a.get("refresh", False)}
        ),
        "movescout_inventory_get": lambda a: client.get(
            f"/leads/{a['leadId']}/inventory",
            params={
                "estimateId": a.get("estimateId"),
                "includeSummary": a.get("includeSummary", True),
                "shippingOnly": a.get("shippingOnly", False),
            },
        ),
        "movescout_estimates_segments_list": lambda a: client.get(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/segments"
        ),
        "movescout_estimates_segments_update": lambda a: client.post(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/segments",
            json=a["segments"],
        ),
        "movescout_estimates_extra_stops_save": lambda a: client.post(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/extra-stops",
            json=a["stops"],
        ),
        "movescout_sts_agent_sales_reps": lambda a: client.get(
            f"/leads/{a['leadId']}/sts/agent-sales-reps"
        ),
        "movescout_sts_reg_details": lambda a: client.get(
            f"/leads/{a['leadId']}/sts/reg-details"
        ),
        "movescout_estimates_reports_list": lambda a: client.get(
            f"/leads/{a['leadId']}/estimates/{a['estimateId']}/reports"
        ),
        "movescout_reference_email_templates": lambda a: client.get(
            "/reference/email-templates", params={"agencyId": a["agencyId"]}
        ),
    }

    if name not in routes:
        raise ValueError(f"Unknown tool: {name}")

    response = await routes[name](arguments)
    response.raise_for_status()
    return response.json()

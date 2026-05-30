from typing import Any

from app.movescout.client import MoveScoutClient
from app.movescout.filters import build_kendo_filter, current_http_date
from app.movescout.paging import movescout_skip_count


async def get_activities(
    client: MoveScoutClient,
    *,
    lead_id: str | None = None,
    filters: list[dict[str, Any]] | None = None,
    page: int = 1,
    page_size: int = 500,
) -> Any:
    payload: dict[str, Any] = {
        "skipCount": movescout_skip_count(page, page_size),
        "maxResultCount": page_size,
        "compositeFilterDescriptorObj": {
            "logic": "and",
            "filters": filters or [],
        },
    }
    if lead_id:
        payload["leadId"] = lead_id

    return await client.request(
        "POST",
        "/api/services/app/Activity/GetAllActivitiesWithCombineData",
        json=payload,
    )


async def create_or_update_activity(client: MoveScoutClient, activity: dict[str, Any]) -> Any:
    return await client.request(
        "POST",
        "/api/services/app/Activity/CreateOrUpdateActivity",
        json=activity,
    )


def build_survey_activity_payload(
    lead: dict[str, Any],
    *,
    survey_date: str,
    survey_duration_hours: int,
    survey_type: str,
    assignee_id: int,
) -> dict[str, Any]:
    first_name = lead.get("firstName", "")
    last_name = lead.get("lastName", "")
    city = lead.get("city", "")
    state = lead.get("state", "")
    move_type = lead.get("moveTypeName") or lead.get("moveType") or ""

    activity_name = f"{last_name}, {first_name}, {city}, {state}, {move_type}"
    description = (
        f"<p>Survey scheduled for {survey_date}</p>"
        f"<p>Type: {survey_type}</p>"
        f"<p>Duration: {survey_duration_hours} hours</p>"
    )

    return {
        "leadId": lead.get("id") or lead.get("leadId"),
        "activityName": activity_name,
        "description": description,
        "activityStart": survey_date,
        "activityEnd": survey_date,
        "activityType": 1,
        "assigneeId": assignee_id,
        "durationHours": survey_duration_hours,
        "surveyType": survey_type,
        "date": current_http_date(),
    }


def build_activity_date_filters(
    start_date: str | None = None,
    end_date: str | None = None,
    activity_type: int | None = None,
    lead_id: str | None = None,
) -> list[dict[str, Any]]:
    filters: list[dict[str, Any]] = []

    if start_date:
        filters.append(build_kendo_filter("activityStart", "gte", start_date))
    if end_date:
        filters.append(build_kendo_filter("activityStart", "lte", end_date))
    if activity_type is not None:
        filters.append(build_kendo_filter("activityType", "eq", activity_type))
    if lead_id:
        filters.append(build_kendo_filter("leadId", "eq", lead_id))

    return filters


def extract_activity_list(response: Any) -> tuple[list[dict[str, Any]], int]:
    result = response.get("result", response) if isinstance(response, dict) else {}
    items = result.get("items") or result.get("data") or []
    total = result.get("totalCount") or result.get("total") or len(items)
    return items, int(total)

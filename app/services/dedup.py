from typing import Any


def deduplicate_latest_per_lead(activities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_lead: dict[Any, dict[str, Any]] = {}

    for activity in activities:
        lead_id = activity.get("leadId")
        if lead_id is None:
            continue

        existing = by_lead.get(lead_id)
        if not existing:
            by_lead[lead_id] = activity
            continue

        current_start = activity.get("activityStart") or ""
        existing_start = existing.get("activityStart") or ""
        if current_start > existing_start:
            by_lead[lead_id] = activity

    return list(by_lead.values())

from typing import Any

from app.config import get_settings


def deep_merge(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in updates.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def apply_lead_defaults(lead: dict[str, Any]) -> dict[str, Any]:
    defaults: dict[str, Any] = {"mobileSyncFlag": True}
    tenant_id = get_settings().movescout_tenant_id
    if tenant_id is not None:
        defaults["tenantId"] = tenant_id
    return deep_merge(defaults, lead)

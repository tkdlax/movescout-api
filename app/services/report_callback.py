import ipaddress
import logging
from urllib.parse import urlparse
from uuid import UUID

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

_BLOCKED_HOSTS = frozenset({"localhost"})


def validate_callback_url(url: str) -> str:
    """Validate a client-supplied webhook URL (SSRF-safe enough for v1)."""
    cleaned = url.strip()
    if not cleaned:
        raise ValueError("callbackUrl cannot be empty")

    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("callbackUrl must use http or https")
    if not parsed.hostname:
        raise ValueError("callbackUrl must include a host")

    settings = get_settings()
    if settings.is_production and parsed.scheme != "https":
        raise ValueError("callbackUrl must use https in production")

    host = parsed.hostname.lower()
    if host in _BLOCKED_HOSTS:
        raise ValueError("callbackUrl cannot target localhost")

    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved:
            raise ValueError("callbackUrl cannot target a private or reserved address")

    return cleaned


async def notify_report_callback(
    *,
    callback_url: str,
    report_id: UUID,
    status: str,
    expires_at,
    filename: str,
    error: str | None = None,
) -> None:
    settings = get_settings()
    payload = {
        "reportId": str(report_id),
        "status": status,
        "expiresAt": expires_at.isoformat(),
        "filename": filename,
        "error": error,
    }
    headers = {"Content-Type": "application/json"}
    if settings.report_callback_secret:
        headers["Authorization"] = f"Bearer {settings.report_callback_secret}"

    try:
        async with httpx.AsyncClient(timeout=settings.report_callback_timeout_seconds) as client:
            response = await client.post(callback_url, json=payload, headers=headers)
            response.raise_for_status()
        logger.info("Report callback delivered for %s to %s", report_id, callback_url)
    except Exception:
        logger.exception("Report callback failed for %s to %s", report_id, callback_url)

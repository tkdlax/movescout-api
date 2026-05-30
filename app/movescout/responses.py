from typing import Any

from app.movescout.client import MoveScoutError


def parse_abp_response(response: Any, *, action: str = "request") -> Any:
    """Extract result from ABP-style JSON or raise MoveScoutError on business failure."""
    if not isinstance(response, dict):
        return response

    if response.get("success") is False:
        err = response.get("error") or {}
        message = err.get("message") or err.get("details") or response
        raise MoveScoutError(
            f"MoveScout {action} failed: {message}",
            status_code=502,
            code="MOVESCOUT_BUSINESS_ERROR",
        )

    if "result" in response:
        return response["result"]

    return response

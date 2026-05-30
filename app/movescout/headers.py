"""Browser-like headers for outbound MoveScout Pro API requests."""

from app.config import get_settings

# Chrome on Windows — match what the MoveScout web app sends.
DEFAULT_MOVESCOUT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
)

MOVESCOUT_USER_AGENT = DEFAULT_MOVESCOUT_USER_AGENT


def movescout_request_headers(*, access_token: str | None = None) -> dict[str, str]:
    """
    Headers that mirror a real browser calling movescoutproapi.sirva.com.
    Used for authenticate (no token) and all authenticated API calls.
    """
    settings = get_settings()
    origin = settings.movescout_origin.rstrip("/")

    headers: dict[str, str] = {
        "User-Agent": settings.movescout_user_agent,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json-patch+json",
        "Origin": origin,
        "Referer": f"{origin}/",
        "Sec-CH-UA": '"Google Chrome";v="147", "Chromium";v="147", "Not_A Brand";v="24"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
    }

    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    return headers

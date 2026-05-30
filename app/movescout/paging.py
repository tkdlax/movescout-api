"""MoveScout pagination: skipCount offsets and page planning."""

# Probe request: skipCount=0, maxResultCount=1 to read totalCount only.
MOVESCOUT_PROBE_MAX_RESULT = 1


def movescout_skip_count(page: int, batch_size: int) -> int:
    """Convert 1-based page to MoveScout skipCount (0-based row offset)."""
    return max(0, (page - 1) * batch_size)


def movescout_page_count(total: int, batch_size: int) -> int:
    """Number of MoveScout pages needed to fetch `total` rows at `batch_size` per page."""
    if total <= 0 or batch_size <= 0:
        return 0
    return (total + batch_size - 1) // batch_size

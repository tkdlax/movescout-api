import csv
import io
from collections.abc import AsyncIterator
from typing import Any


def flatten_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return str(value)
    return str(value)


def resolve_name_fields(
    record: dict[str, Any], lov_cache: dict[str, dict[Any, str]] | None = None
) -> dict[str, Any]:
    if not lov_cache:
        return record

    resolved = dict(record)
    for key, value in list(resolved.items()):
        if key.endswith("Name") and value is None:
            id_key = key[:-4] + "Id" if key.endswith("Name") else None
            if id_key and id_key in resolved:
                lov_key = id_key.replace("Id", "")
                lookup = lov_cache.get(lov_key, {})
                resolved[key] = lookup.get(resolved[id_key], "")
    return resolved


def leads_to_csv_rows(
    leads: list[dict[str, Any]],
    lov_cache: dict[str, dict[Any, str]] | None = None,
) -> tuple[list[str], list[list[str]]]:
    if not leads:
        return [], []

    resolved = [resolve_name_fields(lead, lov_cache) for lead in leads]
    fieldnames = sorted({key for lead in resolved for key in lead.keys()})
    rows = [[flatten_value(lead.get(field)) for field in fieldnames] for lead in resolved]
    return fieldnames, rows


def generate_csv_content(fieldnames: list[str], rows: list[list[str]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    if fieldnames:
        writer.writerow(fieldnames)
    writer.writerows(rows)
    return buffer.getvalue()


async def stream_csv(
    fieldnames: list[str],
    rows: list[list[str]],
) -> AsyncIterator[str]:
    yield generate_csv_content(fieldnames, rows)

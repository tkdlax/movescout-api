from typing import Any

SURVEY_ITEM_FIELDS = (
    "id",
    "estimatesId",
    "articleId",
    "articleName",
    "articleNameFr",
    "articleCode",
    "roomId",
    "roomName",
    "segmentId",
    "shippingQty",
    "notShippingQty",
    "weight",
    "cube",
    "shippingTotal",
    "length",
    "width",
    "height",
    "packing",
    "unpacking",
    "articleNotes",
    "make",
    "year",
    "model",
    "bulky",
    "carton",
    "pbo",
    "crateFlag",
    "isCustomArticle",
    "isActive",
    "isDeleted",
    "isSaved",
    "creationTime",
    "lastModificationTime",
    "articleUpload",
    "allianceCratingUncratingOriginDestinationDetail",
)


def _num(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _int(value: Any) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def normalize_survey_item(item: dict[str, Any]) -> dict[str, Any]:
    return {field: item.get(field) for field in SURVEY_ITEM_FIELDS if field in item}


def item_ships(item: dict[str, Any]) -> bool:
    qty = item.get("shippingQty")
    if qty is None:
        return False
    return _int(qty) > 0


def compute_room_totals(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "shippingQty": sum(_int(i.get("shippingQty")) for i in items),
        "weight": sum(_num(i.get("weight")) for i in items),
        "cube": sum(_num(i.get("cube")) for i in items),
        "shippingTotal": sum(_num(i.get("shippingTotal")) for i in items),
    }


def _summary_index(room_summaries: list[dict[str, Any]] | None) -> dict[int, dict[str, Any]]:
    if not room_summaries:
        return {}
    return {int(r["roomId"]): r for r in room_summaries if r.get("roomId") is not None}


def _totals_close(
    computed: dict[str, Any],
    summary: dict[str, Any],
    field_map: dict[str, str],
) -> bool:
    for computed_key, summary_key in field_map.items():
        if abs(_num(computed.get(computed_key)) - _num(summary.get(summary_key))) > 0.01:
            return False
    return True


def group_survey_by_room(
    survey_items: list[dict[str, Any]],
    *,
    shipping_only: bool = False,
    room_summaries: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    filtered = [i for i in survey_items if item_ships(i)] if shipping_only else list(survey_items)
    summary_by_room = _summary_index(room_summaries)
    warnings: list[str] = []

    rooms_map: dict[int, dict[str, Any]] = {}
    for item in filtered:
        room_id = item.get("roomId")
        if room_id is None:
            continue
        rid = int(room_id)
        if rid not in rooms_map:
            rooms_map[rid] = {
                "roomId": rid,
                "roomName": item.get("roomName"),
                "items": [],
            }
        rooms_map[rid]["items"].append(normalize_survey_item(item))

    rooms: list[dict[str, Any]] = []
    for rid in sorted(rooms_map.keys(), key=lambda x: rooms_map[x].get("roomName") or ""):
        room = rooms_map[rid]
        items = room["items"]
        totals = compute_room_totals(items)
        room["itemCount"] = len(items)
        room["totals"] = totals

        msp_summary = summary_by_room.get(rid)
        if msp_summary is not None:
            room["summaryFromMoveScout"] = msp_summary
            if not _totals_close(
                totals,
                msp_summary,
                {
                    "shippingQty": "sumShippingQuantity",
                    "weight": "sumWeight",
                    "cube": "sumCube",
                    "shippingTotal": "sumShippingTotal",
                },
            ):
                warnings.append(
                    f"Room {room.get('roomName')!r} (id={rid}): "
                    "computed totals differ from MoveScout summary"
                )

        rooms.append(room)

    grand = {
        "itemCount": sum(r["itemCount"] for r in rooms),
        "shippingQty": sum(r["totals"]["shippingQty"] for r in rooms),
        "weight": sum(r["totals"]["weight"] for r in rooms),
        "cube": sum(r["totals"]["cube"] for r in rooms),
        "shippingTotal": sum(r["totals"]["shippingTotal"] for r in rooms),
    }

    return rooms, warnings, grand


def build_inventory_response(
    *,
    lead_id: str,
    estimate_dto: dict[str, Any],
    primary_meta: dict[str, Any] | None = None,
    summary_result: dict[str, Any] | None = None,
    shipping_only: bool = False,
) -> dict[str, Any]:
    survey = estimate_dto.get("leadSurveyDto") or []
    if not isinstance(survey, list):
        survey = []

    room_summaries = None
    if summary_result:
        room_summaries = summary_result.get("leadEstimateRoomSummaryDto")

    rooms, warnings, grand_totals = group_survey_by_room(
        survey,
        shipping_only=shipping_only,
        room_summaries=room_summaries,
    )

    estimate_id = estimate_dto.get("id") or estimate_dto.get("estimateId")
    if primary_meta and not estimate_id:
        estimate_id = primary_meta.get("estimateId")

    primary = primary_meta or {}
    response: dict[str, Any] = {
        "leadId": int(lead_id) if str(lead_id).isdigit() else lead_id,
        "estimateId": estimate_id,
        "estimateName": estimate_dto.get("estimateName") or primary.get("estimateName"),
        "isPrimaryEstimate": estimate_dto.get("isPrimaryEstimate", True),
        "isEstimateWithInventory": estimate_dto.get("isEstimateWithInventory", bool(survey)),
        "estimateStatus": estimate_dto.get("estimateStatus"),
        "weight": estimate_dto.get("weight"),
        "density": estimate_dto.get("density"),
        "miles": estimate_dto.get("miles"),
        "effectiveDate": estimate_dto.get("effectiveDate") or primary.get("effectiveDate"),
        "validThruDate": estimate_dto.get("validThruDate") or primary.get("validThruDate"),
        "tariffName": estimate_dto.get("tariffName") or primary.get("tariffName"),
        "estimateNotes": estimate_dto.get("estimateNotes"),
        "rooms": rooms,
        "grandTotals": grand_totals,
    }

    if warnings:
        response["warnings"] = warnings

    return response

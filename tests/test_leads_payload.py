from unittest.mock import AsyncMock, MagicMock

import pytest

from app.movescout.filters import build_kendo_filter, prepare_lead_filters
from app.movescout.leads import build_get_all_lead_payload, get_all_leads


def test_prepare_lead_filters_passthrough_preserves_operator_and_value_types():
    raw = [
        {
            "field": "creationTime",
            "operator": "eq",
            "value": {"id": 8, "value": "3"},
            "condition": "and",
            "date": "Wed, 10 Jun 2026 06:00:00 GMT",
        }
    ]
    filters = prepare_lead_filters(raw)
    assert filters[0]["operator"] == "eq"
    assert filters[0]["value"] == {"id": 8, "value": "3"}
    assert filters[0]["date"] == "Wed, 10 Jun 2026 06:00:00 GMT"


def test_build_get_all_lead_payload_matches_movescout_spa():
    filters = [build_kendo_filter("creationTime", "eq", {"id": 8, "value": "3"})]
    payload = build_get_all_lead_payload(
        default_filter=0,
        filters=filters,
        page=1,
        page_size=500,
    )
    assert payload["name"] == ""
    assert payload["logic"] == "and"
    assert payload["bulkList"] == []
    assert payload["defaultFilterLead"] == 0
    assert "sortField" not in payload  # sortField only included when specified
    assert payload["maxResultCount"] == 500
    assert payload["skipCount"] == 0
    assert payload["filters"] == filters


def test_build_get_all_lead_payload_with_sort_field():
    payload = build_get_all_lead_payload(
        default_filter=0,
        sort_field="creationTime",
        sort_dir="asc",
    )
    assert payload["sortField"] == "creationTime"
    assert payload["sortDir"] == "asc"


def test_build_get_all_lead_payload_empty_logic_baseline():
    """Wire format: logic='' when no filters (baseline query)."""
    payload = build_get_all_lead_payload(default_filter=0, logic="")
    assert payload["logic"] == ""  # Empty logic for baseline, per P11 wire captures


@pytest.mark.asyncio
async def test_get_all_leads_posts_spa_payload():
    client = MagicMock()
    client.request = AsyncMock(return_value={"result": {"items": [], "totalCount": 0}})

    filters = [build_kendo_filter("creationTime", "eq", {"id": 8, "value": "3"})]
    await get_all_leads(
        client,
        default_filter=0,
        filters=filters,
        page=1,
        page_size=500,
    )

    payload = client.request.await_args.kwargs["json"]
    assert payload["logic"] == "and"
    assert "sortField" not in payload  # sortField only included when specified
    assert payload["sortDescriptor"] == {}  # Always empty object per P11 wire format


class TestP11ExpandedFilterFields:
    """P11 expanded filter fields tests - live-proven columns."""

    def test_p11_contains_filter_leadlmp_lmpid(self):
        """LMP ID filter with contains operator."""
        f = build_kendo_filter("leadLMP.lmpId", "contains", "ABC123")
        assert f["field"] == "leadLMP.lmpId"
        assert f["operator"] == "contains"
        assert f["value"] == "ABC123"

    def test_p11_contains_filter_created_user_name(self):
        """Created By filter with contains operator."""
        f = build_kendo_filter("createdUserName", "contains", "admin")
        assert f["field"] == "createdUserName"
        assert f["operator"] == "contains"
        assert f["value"] == "admin"

    def test_p11_eq_filter_appointment_type_id(self):
        """Appointment Type filter with eq operator."""
        f = build_kendo_filter("appointmentTypeId", "eq", 1)
        assert f["field"] == "appointmentTypeId"
        assert f["operator"] == "eq"
        assert f["value"] == 1

    def test_p11_eq_filter_mobile_sync_flag(self):
        """Mobile Sync Flag filter with eq true."""
        f = build_kendo_filter("mobileSyncFlag", "eq", True)
        assert f["field"] == "mobileSyncFlag"
        assert f["operator"] == "eq"
        assert f["value"] is True

    def test_p11_eq_filter_is_qualified_lead(self):
        """Is Qualified Lead filter with eq true."""
        f = build_kendo_filter("isQualifiedLead", "eq", True)
        assert f["field"] == "isQualifiedLead"
        assert f["operator"] == "eq"
        assert f["value"] is True

    def test_p11_eq_filter_estimate_total(self):
        """Estimate Total filter with eq numeric."""
        f = build_kendo_filter("estimateTotal", "eq", 2771.90)
        assert f["field"] == "estimateTotal"
        assert f["operator"] == "eq"
        assert f["value"] == 2771.90

    def test_p11_eq_filter_funded_id(self):
        """Funded ID filter with eq operator."""
        f = build_kendo_filter("fundedId", "eq", 1)
        assert f["field"] == "fundedId"
        assert f["operator"] == "eq"
        assert f["value"] == 1

    def test_p11_eq_filter_dwelling_type_id(self):
        """Dwelling Type filter with eq operator."""
        f = build_kendo_filter("dwellingTypeId", "eq", 2)
        assert f["field"] == "dwellingTypeId"
        assert f["operator"] == "eq"
        assert f["value"] == 2

    def test_p11_eq_filter_non_conforming_flag(self):
        """Non-Conforming Flag filter (nested path)."""
        f = build_kendo_filter("leadNonConforming.nonConformingFlag", "eq", True)
        assert f["field"] == "leadNonConforming.nonConformingFlag"
        assert f["operator"] == "eq"
        assert f["value"] is True

    def test_p11_eq_filter_canada_gov_move(self):
        """Canada Gov Move filter (nested path)."""
        f = build_kendo_filter("leadMoSys.canadaGovMove", "eq", True)
        assert f["field"] == "leadMoSys.canadaGovMove"
        assert f["operator"] == "eq"
        assert f["value"] is True

    def test_p11_date_preset_load_from_date(self):
        """Load From Date filter with date preset."""
        f = build_kendo_filter("leadMoveDate.loadFromDate", "eq", {"id": 5, "value": 30})
        assert f["field"] == "leadMoveDate.loadFromDate"
        assert f["operator"] == "eq"
        assert f["value"] == {"id": 5, "value": 30}

    def test_p11_date_preset_effective_date(self):
        """Effective Date filter with date preset."""
        f = build_kendo_filter("primaryLeadEstimate.effectiveDate", "eq", {"id": 5, "value": 30})
        assert f["field"] == "primaryLeadEstimate.effectiveDate"
        assert f["operator"] == "eq"
        assert f["value"] == {"id": 5, "value": 30}

    def test_p11_date_preset_valid_thru_date(self):
        """Valid Thru Date filter with date preset (nested path)."""
        f = build_kendo_filter("primaryLeadEstimate.validThruDate", "eq", {"id": 5, "value": 30})
        assert f["field"] == "primaryLeadEstimate.validThruDate"
        assert f["operator"] == "eq"
        assert f["value"] == {"id": 5, "value": 30}

    def test_p11_date_preset_last_modification_time(self):
        """Last Modification Time filter with date preset."""
        f = build_kendo_filter("lastModificationTime", "eq", {"id": 5, "value": 30})
        assert f["field"] == "lastModificationTime"
        assert f["operator"] == "eq"
        assert f["value"] == {"id": 5, "value": 30}

    def test_p11_combined_filters_packet_15(self):
        """Combined filters scenario (packet 15 style)."""
        raw = [
            {"field": "leadCustomerDetail.lastName", "op": "contains", "value": "Smith"},
            {"field": "isQualifiedLead", "op": "eq", "value": True},
            {"field": "assignedDate", "op": "eq", "value": {"id": 5, "value": 30}},
        ]
        filters = prepare_lead_filters(raw, logic="and")
        assert len(filters) == 3
        assert filters[0]["field"] == "leadCustomerDetail.lastName"
        assert filters[0]["operator"] == "contains"
        assert filters[1]["field"] == "isQualifiedLead"
        assert filters[1]["value"] is True
        assert filters[2]["field"] == "assignedDate"
        assert filters[2]["value"] == {"id": 5, "value": 30}

    def test_p11_disallowed_field_raises_error(self):
        """Fields not in allowlist should raise ValueError."""
        with pytest.raises(ValueError, match="not allowed"):
            build_kendo_filter("unknownField", "contains", "test")


class TestP11Packets28To38FilterFields:
    """P11 packets 28-38 expanded filter fields tests - live-proven columns."""

    # CONTAINS fields

    def test_p11_contains_filter_booker_name(self):
        """Booking Agent Name filter with contains operator."""
        f = build_kendo_filter("bookerName", "contains", "Bailey's")
        assert f["field"] == "bookerName"
        assert f["operator"] == "contains"
        assert f["value"] == "Bailey's"

    def test_p11_contains_filter_coordinator_name(self):
        """Coordinator filter with contains operator."""
        f = build_kendo_filter("coordinatorName", "contains", "Smith")
        assert f["field"] == "coordinatorName"
        assert f["operator"] == "contains"
        assert f["value"] == "Smith"

    def test_p11_contains_filter_modified_user_name(self):
        """Modified By filter with contains operator."""
        f = build_kendo_filter("modifiedUserName", "contains", "admin")
        assert f["field"] == "modifiedUserName"
        assert f["operator"] == "contains"
        assert f["value"] == "admin"

    def test_p11_contains_filter_local_carrier_id(self):
        """Local Carrier filter with contains operator (UI gap: blank cells → totalCount 0)."""
        f = build_kendo_filter("localCarrierId", "contains", "123")
        assert f["field"] == "localCarrierId"
        assert f["operator"] == "contains"
        assert f["value"] == "123"

    # EQ fields

    def test_p11_eq_filter_created_source(self):
        """Created Source filter with eq operator."""
        f = build_kendo_filter("createdSource", "eq", 5)
        assert f["field"] == "createdSource"
        assert f["operator"] == "eq"
        assert f["value"] == 5

    def test_p11_eq_filter_mobile_sync_status_id(self):
        """Mobile Sync Status filter with eq operator."""
        f = build_kendo_filter("mobileSyncStatusId", "eq", 204)
        assert f["field"] == "mobileSyncStatusId"
        assert f["operator"] == "eq"
        assert f["value"] == 204

    def test_p11_eq_filter_lost_reason_id(self):
        """Lost Reason filter with eq operator."""
        f = build_kendo_filter("lostReasonId", "eq", 13)
        assert f["field"] == "lostReasonId"
        assert f["operator"] == "eq"
        assert f["value"] == 13

    def test_p11_eq_filter_transfer_type_id(self):
        """Transfer Type filter (nested leadLMP path) with eq operator."""
        f = build_kendo_filter("leadLMP.transferTypeId", "eq", 1063)
        assert f["field"] == "leadLMP.transferTypeId"
        assert f["operator"] == "eq"
        assert f["value"] == 1063

    # DATE PRESET fields

    def test_p11_date_preset_load_to_date(self):
        """Load To Date filter with date preset (Previous Month)."""
        f = build_kendo_filter("leadMoveDate.loadToDate", "eq", {"id": 5, "value": 30})
        assert f["field"] == "leadMoveDate.loadToDate"
        assert f["operator"] == "eq"
        assert f["value"] == {"id": 5, "value": 30}

    def test_p11_date_preset_expected_deliver_date(self):
        """Expected Delivery Date filter with date preset (Previous Month)."""
        f = build_kendo_filter("leadMoveDate.expectedDeliverDate", "eq", {"id": 5, "value": 30})
        assert f["field"] == "leadMoveDate.expectedDeliverDate"
        assert f["operator"] == "eq"
        assert f["value"] == {"id": 5, "value": 30}

    def test_p11_date_preset_scheduled_date(self):
        """Appt Created Date (Scheduled Date) filter with date preset."""
        f = build_kendo_filter("leadMoveDate.scheduledDate", "eq", {"id": 5, "value": 30})
        assert f["field"] == "leadMoveDate.scheduledDate"
        assert f["operator"] == "eq"
        assert f["value"] == {"id": 5, "value": 30}

    def test_p11_combined_filters_packets_28_38(self):
        """Combined filters scenario using packets 28-38 fields."""
        raw = [
            {"field": "bookerName", "op": "contains", "value": "Bailey's"},
            {"field": "createdSource", "op": "eq", "value": 5},
            {"field": "leadMoveDate.loadToDate", "op": "eq", "value": {"id": 5, "value": 30}},
        ]
        filters = prepare_lead_filters(raw, logic="and")
        assert len(filters) == 3
        assert filters[0]["field"] == "bookerName"
        assert filters[0]["operator"] == "contains"
        assert filters[1]["field"] == "createdSource"
        assert filters[1]["value"] == 5
        assert filters[2]["field"] == "leadMoveDate.loadToDate"
        assert filters[2]["value"] == {"id": 5, "value": 30}

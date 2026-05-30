from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: UUID
    name: str
    movescout_username: str
    sales_rep_name: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class FilterSpec(BaseModel):
    field: str
    op: str
    value: Any = None


class LeadListRequest(BaseModel):
    """Shared filter/sort params for lead list, page-count, and query endpoints."""

    default_filter: int = Field(default=3, alias="defaultFilter")
    filters: list[FilterSpec] = Field(default_factory=list)
    logic: str = "and"
    max_result_size: int = Field(default=500, alias="maxResultSize", ge=1, le=1000)
    sort_field: str | None = Field(default=None, alias="sortField")
    sort_dir: str = Field(default="desc", alias="sortDir")

    model_config = {"populate_by_name": True}


class LeadQueryRequest(LeadListRequest):
    page: int = Field(default=1, ge=1)
    export: bool = False


class CreateAppointmentRequest(BaseModel):
    survey_date: str = Field(alias="surveyDate")
    survey_duration_hours: int = Field(default=2, alias="surveyDurationHours")
    survey_type: str = Field(default="onsite", alias="surveyType")
    assignee_id: int = Field(alias="assigneeId")

    model_config = {"populate_by_name": True}


class ErrorResponse(BaseModel):
    error: str
    code: str
    request_id: str | None = None


class SalesReportJobCreatedResponse(BaseModel):
    report_id: UUID = Field(alias="reportId")
    status: str
    expires_at: datetime = Field(alias="expiresAt")

    model_config = {"populate_by_name": True}


class SalesReportJobStatusResponse(BaseModel):
    report_id: UUID = Field(alias="reportId")
    status: str
    expires_at: datetime = Field(alias="expiresAt")
    error: str | None = None

    model_config = {"populate_by_name": True}


class SalesReportCreateRequest(BaseModel):
    move_type: str = Field(default="Interstate", alias="moveType")
    start: str | None = None
    end: str | None = None
    location: str = Field(default="Bailey's Moving & Storage")
    goal: float = Field(default=0.40, ge=0.0, le=1.0)
    sales_rep_name: str | None = Field(default=None, alias="salesRepName")
    default_filter: int = Field(default=3, alias="defaultFilter", ge=0, le=12)
    callback_url: str | None = Field(default=None, alias="callbackUrl")

    model_config = {"populate_by_name": True}

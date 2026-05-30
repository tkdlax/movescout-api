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


class LeadQueryRequest(BaseModel):
    default_filter: int = Field(default=3, alias="defaultFilter")
    filters: list[FilterSpec] = Field(default_factory=list)
    logic: str = "and"
    page_size: int = Field(default=500, alias="pageSize", ge=1, le=1000)
    page: int = Field(default=1, ge=1)
    export: bool = False
    sort_field: str | None = Field(default=None, alias="sortField")
    sort_dir: str = Field(default="desc", alias="sortDir")

    model_config = {"populate_by_name": True}


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

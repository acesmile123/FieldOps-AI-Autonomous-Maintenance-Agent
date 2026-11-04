from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.analysis import Confidence, Evidence, Priority, Severity


class WorkOrderStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WorkOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    issue_summary: str
    equipment_type: str | None
    equipment_identifier: str | None
    location: str | None
    reported_symptoms: list[str]
    visual_observations: list[str]
    audio_observations: list[str]
    evidence: list[Evidence]
    inferences: list[str]
    assumptions: list[str]
    unknowns: list[str]
    severity: Severity
    suggested_priority: Priority
    priority_reason: str
    confidence: Confidence
    missing_information: list[str]
    safe_checklist: list[str]
    technician_message_draft: str
    customer_message_draft: str
    safety_flags: list[str]
    transcript: str | None
    status: WorkOrderStatus
    requires_human_review: bool
    agent_run_id: str
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None


class AgentRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    provider: str
    models: list[str]
    started_at: datetime
    completed_at: datetime | None
    duration_ms: int | None
    error_code: str | None
    error_message_safe: str | None


class AgentEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_run_id: str
    event_type: str
    stage: str
    status: str
    summary: str
    created_at: datetime


class MediaAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    work_order_id: str
    kind: str
    original_filename: str
    mime_type: str
    size_bytes: int
    created_at: datetime


class WorkOrderDetail(BaseModel):
    work_order: WorkOrderRead
    media_assets: list[MediaAssetRead]
    agent_run: AgentRunRead
    events: list[AgentEventRead]


class WorkOrderList(BaseModel):
    items: list[WorkOrderRead]
    total: int
    limit: int
    offset: int


class IntakeResult(BaseModel):
    work_order: WorkOrderRead
    agent_run: AgentRunRead
    mode: str
    notice: str | None
    stages: list


class WorkOrderUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    issue_summary: str | None = Field(default=None, min_length=1)
    equipment_type: str | None = Field(default=None, max_length=200)
    equipment_identifier: str | None = Field(default=None, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    suggested_priority: Priority | None = None
    priority_reason: str | None = Field(default=None, min_length=1)
    safe_checklist: list[str] | None = None
    missing_information: list[str] | None = None
    technician_message_draft: str | None = None
    customer_message_draft: str | None = None

    @field_validator("safe_checklist", "missing_information")
    @classmethod
    def nonblank_items(cls, value):
        if value is not None and any(not item.strip() for item in value):
            raise ValueError("List items cannot be blank")
        return value

    @model_validator(mode="after")
    def nonempty_patch(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update")
        required_fields = {
            "title", "issue_summary", "suggested_priority", "priority_reason",
            "safe_checklist", "missing_information",
            "technician_message_draft", "customer_message_draft",
        }
        if any(getattr(self, name) is None for name in required_fields & self.model_fields_set):
            raise ValueError("Required work-order fields cannot be null")
        return self


class StatusUpdate(BaseModel):
    status: WorkOrderStatus

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EvidenceSource(StrEnum):
    USER_TEXT = "user_text"
    TRANSCRIPT = "transcript"
    IMAGE = "image"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class Priority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Confidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: EvidenceSource
    claim: str = Field(min_length=1)
    supporting_detail: str | None


class MaintenanceAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue_summary: str = Field(min_length=1)
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
    priority_reason: str = Field(min_length=1)
    confidence: Confidence
    missing_information: list[str]
    safe_checklist: list[str]
    technician_message_draft: str
    customer_message_draft: str
    safety_flags: list[str]
    requires_human_review: Literal[True]


class ProcessingStage(BaseModel):
    name: Literal["validation", "transcription", "analysis", "safety"]
    status: Literal["succeeded", "failed", "skipped"]


class AnalysisResponse(BaseModel):
    analysis: MaintenanceAnalysis
    transcript: str | None
    mode: Literal["live", "mock"]
    provider: Literal["meta", "mock"]
    models: list[str]
    stages: list[ProcessingStage]
    notice: str | None

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.db.session import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator):
    """Store ISO UTC text so SQLite round-trips timezone-aware datetimes."""

    impl = String(40)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware")
        return value.astimezone(timezone.utc).isoformat()

    def process_result_value(self, value, dialect):
        return datetime.fromisoformat(value) if value is not None else None


def new_id() -> str:
    return str(uuid4())


class AgentRun(Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        CheckConstraint("status IN ('pending','running','succeeded','failed')", name="ck_agent_run_status"),
        CheckConstraint("provider IN ('meta','mock')", name="ck_agent_run_provider"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    provider: Mapped[str] = mapped_column(String(10), nullable=False)
    models: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_message_safe: Mapped[str | None] = mapped_column(String(300))

    work_orders: Mapped[list["WorkOrder"]] = relationship(back_populates="agent_run")
    events: Mapped[list["AgentEvent"]] = relationship(
        back_populates="agent_run", cascade="all, delete-orphan", order_by="AgentEvent.id"
    )


class WorkOrder(Base):
    __tablename__ = "work_orders"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','approved','in_progress','completed','cancelled')",
            name="ck_work_order_status",
        ),
        Index("ix_work_orders_status_created", "status", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    issue_summary: Mapped[str] = mapped_column(Text, nullable=False)
    equipment_type: Mapped[str | None] = mapped_column(String(200))
    equipment_identifier: Mapped[str | None] = mapped_column(String(200))
    location: Mapped[str | None] = mapped_column(String(200))
    reported_symptoms: Mapped[list] = mapped_column(JSON, nullable=False)
    visual_observations: Mapped[list] = mapped_column(JSON, nullable=False)
    audio_observations: Mapped[list] = mapped_column(JSON, nullable=False)
    evidence: Mapped[list] = mapped_column(JSON, nullable=False)
    inferences: Mapped[list] = mapped_column(JSON, nullable=False)
    assumptions: Mapped[list] = mapped_column(JSON, nullable=False)
    unknowns: Mapped[list] = mapped_column(JSON, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    suggested_priority: Mapped[str] = mapped_column(String(20), nullable=False)
    priority_reason: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), nullable=False)
    missing_information: Mapped[list] = mapped_column(JSON, nullable=False)
    safe_checklist: Mapped[list] = mapped_column(JSON, nullable=False)
    technician_message_draft: Mapped[str] = mapped_column(Text, nullable=False)
    customer_message_draft: Mapped[str] = mapped_column(Text, nullable=False)
    safety_flags: Mapped[list] = mapped_column(JSON, nullable=False)
    transcript: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    requires_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    agent_run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utc_now)
    approved_at: Mapped[datetime | None] = mapped_column(UTCDateTime)

    agent_run: Mapped[AgentRun] = relationship(back_populates="work_orders")
    media_assets: Mapped[list["MediaAsset"]] = relationship(
        back_populates="work_order", cascade="all, delete-orphan"
    )


class MediaAsset(Base):
    __tablename__ = "media_assets"
    __table_args__ = (
        CheckConstraint("kind IN ('image','audio')", name="ck_media_kind"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    work_order_id: Mapped[str] = mapped_column(ForeignKey("work_orders.id"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(10), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(200), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(50), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utc_now)

    work_order: Mapped[WorkOrder] = relationship(back_populates="media_assets")


class AgentEvent(Base):
    __tablename__ = "agent_events"
    __table_args__ = (Index("ix_agent_events_run_created", "agent_run_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    summary: Mapped[str] = mapped_column(String(240), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False, default=utc_now)

    agent_run: Mapped[AgentRun] = relationship(back_populates="events")

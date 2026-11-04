import re

from app.models import AgentEvent, AgentRun, WorkOrder
from app.models.entities import utc_now
from app.schemas.analysis import AnalysisResponse
from app.schemas.work_order import WorkOrderStatus, WorkOrderUpdate
from app.services.agent.safety import UNSAFE_ACTION


class WorkOrderConflict(Exception):
    pass


class WorkOrderService:
    @staticmethod
    def from_analysis(result: AnalysisResponse, run: AgentRun) -> WorkOrder:
        analysis = result.analysis
        summary = re.sub(r"\s+", " ", analysis.issue_summary).strip()
        location = re.sub(r"\s+", " ", analysis.location or "").strip()
        title = f"{location} — {summary}" if location and location.casefold() not in summary.casefold() else summary
        return WorkOrder(
            title=title[:200],
            issue_summary=analysis.issue_summary,
            equipment_type=analysis.equipment_type,
            equipment_identifier=analysis.equipment_identifier,
            location=analysis.location,
            reported_symptoms=analysis.reported_symptoms,
            visual_observations=analysis.visual_observations,
            audio_observations=analysis.audio_observations,
            evidence=[item.model_dump(mode="json") for item in analysis.evidence],
            inferences=analysis.inferences,
            assumptions=analysis.assumptions,
            unknowns=analysis.unknowns,
            severity=analysis.severity.value,
            suggested_priority=analysis.suggested_priority.value,
            priority_reason=analysis.priority_reason,
            confidence=analysis.confidence.value,
            missing_information=analysis.missing_information,
            safe_checklist=analysis.safe_checklist,
            technician_message_draft=analysis.technician_message_draft,
            customer_message_draft=analysis.customer_message_draft,
            safety_flags=analysis.safety_flags,
            transcript=result.transcript,
            status=WorkOrderStatus.DRAFT.value,
            requires_human_review=True,
            agent_run=run,
        )

    @staticmethod
    def edit(order: WorkOrder, patch: WorkOrderUpdate) -> None:
        if order.status != WorkOrderStatus.DRAFT:
            raise WorkOrderConflict("Only draft work orders can be edited.")
        changes = patch.model_dump(exclude_unset=True)
        safe_text = changes.get("safe_checklist", []) + [
            changes.get("technician_message_draft", ""),
            changes.get("customer_message_draft", ""),
        ]
        if any(UNSAFE_ACTION.search(item) for item in safe_text):
            raise ValueError("Update contains an unsafe action.")
        for name, value in changes.items():
            setattr(order, name, value.value if hasattr(value, "value") else value)
        order.updated_at = utc_now()

    @staticmethod
    def approve(order: WorkOrder) -> None:
        if order.status != WorkOrderStatus.DRAFT:
            raise WorkOrderConflict("Only a draft work order can be approved.")
        now = utc_now()
        order.status = WorkOrderStatus.APPROVED.value
        order.approved_at = now
        order.updated_at = now

    @staticmethod
    def change_status(order: WorkOrder, target: WorkOrderStatus) -> None:
        allowed = {
            WorkOrderStatus.DRAFT: {WorkOrderStatus.CANCELLED},
            WorkOrderStatus.APPROVED: {WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.CANCELLED},
            WorkOrderStatus.IN_PROGRESS: {WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED},
        }
        current = WorkOrderStatus(order.status)
        if target not in allowed.get(current, set()):
            raise WorkOrderConflict(f"Cannot change status from {current.value} to {target.value}.")
        order.status = target.value
        order.updated_at = utc_now()


def event(run: AgentRun, event_type: str, stage: str, status: str, summary: str) -> AgentEvent:
    return AgentEvent(agent_run=run, event_type=event_type, stage=stage, status=status, summary=summary)

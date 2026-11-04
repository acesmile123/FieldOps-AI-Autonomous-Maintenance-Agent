from app.schemas.analysis import (
    Confidence, Evidence, EvidenceSource, MaintenanceAnalysis, Priority, Severity,
)


class MockProvider:
    def transcribe(self, _audio: bytes) -> str:
        return "MOCK TRANSCRIPT — demo voice note about an air conditioner needing inspection."

    def analyze(self, description: str, transcript: str | None,
                image: bytes | None) -> MaintenanceAnalysis:
        summary = description.strip() or "Demo voice note requests equipment inspection."
        evidence = []
        if description.strip():
            evidence.append(Evidence(source=EvidenceSource.USER_TEXT,
                                     claim=summary, supporting_detail=None))
        if transcript:
            evidence.append(Evidence(source=EvidenceSource.TRANSCRIPT,
                                     claim=transcript, supporting_detail="Mock transcription"))
        unknowns = ["Asset ID and maintenance history have not been verified."]
        if image is not None:
            unknowns.append("Photo is attached but mock mode does not interpret images.")
        return MaintenanceAnalysis(
            issue_summary=summary,
            equipment_type=None,
            equipment_identifier=None,
            location=None,
            reported_symptoms=[summary],
            visual_observations=[],
            audio_observations=[],
            evidence=evidence,
            inferences=[],
            assumptions=[],
            unknowns=unknowns,
            severity=Severity.UNKNOWN,
            suggested_priority=Priority.NORMAL,
            priority_reason="Mock recommendation for UI development; review the source report.",
            confidence=Confidence.LOW,
            missing_information=["Confirm equipment identifier, location, and impact."],
            safe_checklist=["Confirm the reported location and arrange a qualified technician review."],
            technician_message_draft="MOCK DRAFT — Please review the intake details.",
            customer_message_draft="MOCK DRAFT — Your report has been received for review.",
            safety_flags=[],
            requires_human_review=True,
        )

import re

from app.providers.meta.client import ProviderError
from app.schemas.analysis import EvidenceSource, MaintenanceAnalysis, Priority


UNSAFE_ACTION = re.compile(
    r"\b(open (?:the )?(?:unit|panel|cabinet|cover)|touch (?:the )?(?:wire|wiring|terminal)|"
    r"handle (?:refrigerant|gas)|bypass (?:the )?(?:safety|interlock)|"
    r"climb (?:a |the )?(?:ladder|roof)|repair (?:the )?(?:wiring|compressor))\b",
    re.IGNORECASE,
)
HAZARD = re.compile(
    r"\b(smoke|fire|burning smell|gas leak|exposed wir(?:e|ing)|"
    r"water near (?:electric|wiring|outlet)|refrigerant leak)\b", re.IGNORECASE
)
NONVISUAL_CLAIM = re.compile(
    r"\b(sound|noise|rattl\w*|smell|odor|not cooling|temperature|maintenance history)\b",
    re.IGNORECASE,
)


def validate_safety(analysis: MaintenanceAnalysis, description: str,
                    transcript: str | None, has_image: bool) -> MaintenanceAnalysis:
    sources = {EvidenceSource.USER_TEXT if description.strip() else None,
               EvidenceSource.TRANSCRIPT if transcript else None,
               EvidenceSource.IMAGE if has_image else None}
    if any(item.source not in sources for item in analysis.evidence):
        raise ProviderError("MODEL_OUTPUT_INVALID", "Analysis cited an unavailable evidence source.")
    if not has_image and analysis.visual_observations:
        raise ProviderError("MODEL_OUTPUT_INVALID", "Analysis reported visual evidence without an image.")
    if not transcript and analysis.audio_observations:
        raise ProviderError("MODEL_OUTPUT_INVALID", "Analysis reported audio evidence without a transcript.")
    if any(NONVISUAL_CLAIM.search(item) for item in analysis.visual_observations):
        raise ProviderError("MODEL_OUTPUT_INVALID", "Analysis presented a non-visual symptom as an image observation.")
    if any(NONVISUAL_CLAIM.search(item.claim) for item in analysis.evidence
           if item.source == EvidenceSource.IMAGE):
        raise ProviderError("MODEL_OUTPUT_INVALID", "Analysis cited an image for a non-visual symptom.")
    reported = {item.casefold().strip() for item in analysis.reported_symptoms}
    if any(item.casefold().strip() in reported for item in analysis.visual_observations):
        raise ProviderError("MODEL_OUTPUT_INVALID", "Analysis mixed reported symptoms with visual observations.")
    text_fields = analysis.safe_checklist + [
        analysis.technician_message_draft, analysis.customer_message_draft
    ]
    if any(UNSAFE_ACTION.search(item) for item in text_fields):
        raise ProviderError("UNSAFE_MODEL_OUTPUT", "Analysis contained an unsafe action.")
    supplied_text = f"{description}\n{transcript or ''}"
    if analysis.equipment_identifier and analysis.equipment_identifier.casefold() not in supplied_text.casefold():
        analysis.equipment_identifier = None
        if "Equipment identifier needs confirmation." not in analysis.unknowns:
            analysis.unknowns.append("Equipment identifier needs confirmation.")
    if HAZARD.search(supplied_text):
        flag = "Potential hazard reported; qualified professional escalation required."
        if flag not in analysis.safety_flags:
            analysis.safety_flags.append(flag)
        action = "Escalate to a qualified professional; contact emergency services if there is immediate danger."
        if action not in analysis.safe_checklist:
            analysis.safe_checklist.append(action)
        analysis.suggested_priority = Priority.URGENT
        analysis.priority_reason = "Potential hazard was reported; human review must confirm urgency."
    return analysis

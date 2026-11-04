import base64
import json

from app.core.config import Settings, get_settings
from app.providers.meta.client import MetaClient, ProviderError
from app.schemas.analysis import MaintenanceAnalysis
from app.services.agent.prompts import SYSTEM_PROMPT, user_prompt


class MuseSpark:
    def __init__(self, client: MetaClient, settings: Settings | None = None):
        self.client = client
        self.settings = settings or get_settings()

    def analyze(self, description: str, transcript: str | None,
                image: bytes | None) -> MaintenanceAnalysis:
        content: list[dict] = [
            {"type": "input_text", "text": user_prompt(description, transcript, image is not None)}
        ]
        if image is not None:
            content.append({
                "type": "input_image",
                "image_url": "data:image/jpeg;base64," + base64.b64encode(image).decode("ascii"),
            })
        payload = {
            "model": self.settings.meta_spark_model,
            "input": [
                {"type": "message", "role": "system",
                 "content": [{"type": "input_text", "text": SYSTEM_PROMPT}]},
                {"type": "message", "role": "user", "content": content},
            ],
            "text": {"format": {
                "type": "json_schema",
                "name": "maintenance_analysis",
                "schema": MaintenanceAnalysis.model_json_schema(),
                "strict": True,
            }},
        }
        response = self.client.post("/responses", payload=payload)
        if response.get("status") != "completed":
            raise ProviderError("PROVIDER_INCOMPLETE", "Meta analysis did not complete.")
        texts = [
            part.get("text")
            for item in response.get("output", [])
            if item.get("type") == "message"
            for part in item.get("content", [])
            if part.get("type") == "output_text"
        ]
        if not texts or not isinstance(texts[0], str):
            raise ProviderError("PROVIDER_BAD_RESPONSE", "Meta analysis returned no text.")
        try:
            parsed = json.loads(texts[0])
            return MaintenanceAnalysis.model_validate(parsed)
        except (ValueError, TypeError):
            raise ProviderError("MODEL_OUTPUT_INVALID", "Meta analysis could not be validated.") from None

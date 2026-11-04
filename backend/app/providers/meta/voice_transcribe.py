from app.core.config import Settings, get_settings
from app.providers.meta.client import MetaClient, ProviderError


class MuseVoiceTranscribe:
    def __init__(self, client: MetaClient, settings: Settings | None = None):
        self.client = client
        self.settings = settings or get_settings()

    def transcribe(self, audio: bytes) -> str:
        files = {
            "request": self.client.json_part({
                "model": self.settings.meta_voice_model,
                "audioEncoding": "WAV",
                "mode": "PUSH_TO_TALK",
            }),
            "audio": ("recording.wav", audio, "audio/wav"),
        }
        response = self.client.post("/asr/transcribe", files=files)
        transcript = response.get("transcript")
        if not isinstance(transcript, str):
            raise ProviderError("PROVIDER_BAD_RESPONSE", "Meta transcription returned no transcript.")
        return transcript

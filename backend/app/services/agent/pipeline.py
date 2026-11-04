import io
import wave
from typing import Protocol

from app.core.config import Settings, get_settings
from app.providers.meta.client import MetaClient, ProviderError
from app.providers.meta.muse_spark import MuseSpark
from app.providers.meta.voice_transcribe import MuseVoiceTranscribe
from app.schemas.analysis import AnalysisResponse, MaintenanceAnalysis, ProcessingStage
from app.services.agent.mock import MockProvider
from app.services.agent.safety import validate_safety


class Analyzer(Protocol):
    def analyze(self, description: str, transcript: str | None,
                image: bytes | None) -> MaintenanceAnalysis: ...


class Transcriber(Protocol):
    def transcribe(self, audio: bytes) -> str: ...


class PipelineError(Exception):
    def __init__(self, code: str, message: str, stage: str, status_code: int = 422):
        super().__init__(message)
        self.code, self.message, self.stage, self.status_code = code, message, stage, status_code


def validate_image(image: bytes | None, settings: Settings) -> None:
    if image is None:
        return
    if not image or len(image) > settings.max_image_mb * 1024 * 1024:
        raise PipelineError("INVALID_IMAGE", "JPEG image is empty or too large.", "validation")
    if not (image.startswith(b"\xff\xd8") and image.rstrip().endswith(b"\xff\xd9")):
        raise PipelineError("INVALID_IMAGE", "Upload a valid JPEG image.", "validation")


def validate_audio(audio: bytes | None, settings: Settings) -> None:
    if audio is None:
        return
    if not audio or len(audio) > settings.max_audio_mb * 1024 * 1024:
        raise PipelineError("INVALID_AUDIO", "WAV audio is empty or too large.", "validation")
    try:
        with wave.open(io.BytesIO(audio), "rb") as wav:
            valid = (wav.getnchannels() == 1 and wav.getframerate() in {16000, 24000}
                     and wav.getsampwidth() == 2 and wav.getcomptype() == "NONE"
                     and 0 < wav.getnframes() <= 600 * wav.getframerate())
    except (wave.Error, EOFError):
        valid = False
    if not valid:
        raise PipelineError("INVALID_AUDIO", "Upload mono 16-bit PCM WAV at 16 or 24 kHz, up to 10 minutes.", "validation")


class AnalysisPipeline:
    def __init__(self, settings: Settings | None = None,
                 analyzer: Analyzer | None = None, transcriber: Transcriber | None = None):
        self.settings = settings or get_settings()
        if self.settings.demo_mock_mode:
            mock = MockProvider()
            self.analyzer = analyzer or mock
            self.transcriber = transcriber or mock
        else:
            client = MetaClient(self.settings)
            self.analyzer = analyzer or MuseSpark(client, self.settings)
            self.transcriber = transcriber or MuseVoiceTranscribe(client, self.settings)

    def run(self, description: str, image: bytes | None = None,
            audio: bytes | None = None) -> AnalysisResponse:
        description = description.strip()
        if not description and audio is None:
            raise PipelineError("MISSING_REPORT", "Provide a description or a WAV voice note.", "validation")
        validate_image(image, self.settings)
        validate_audio(audio, self.settings)
        stages = [ProcessingStage(name="validation", status="succeeded")]
        transcript = None
        if audio is not None:
            try:
                transcript = self.transcriber.transcribe(audio)
            except ProviderError as exc:
                raise PipelineError(exc.code, exc.message, "transcription", exc.status_code) from None
            stages.append(ProcessingStage(name="transcription", status="succeeded"))
            if not transcript.strip():
                raise PipelineError("EMPTY_TRANSCRIPT", "No speech was transcribed. Add a description and retry.", "transcription")
        else:
            stages.append(ProcessingStage(name="transcription", status="skipped"))
        for attempt in range(2):
            try:
                analysis = self.analyzer.analyze(description, transcript, image)
            except ProviderError as exc:
                if exc.code == "MODEL_OUTPUT_INVALID" and attempt == 0:
                    continue
                raise PipelineError(exc.code, exc.message, "analysis", exc.status_code) from None
            try:
                analysis = validate_safety(analysis, description, transcript, image is not None)
                break
            except ProviderError as exc:
                if exc.code == "MODEL_OUTPUT_INVALID" and attempt == 0:
                    continue
                raise PipelineError(exc.code, exc.message, "safety", exc.status_code) from None
        stages.append(ProcessingStage(name="analysis", status="succeeded"))
        stages.append(ProcessingStage(name="safety", status="succeeded"))
        mock = self.settings.demo_mock_mode
        return AnalysisResponse(
            analysis=analysis,
            transcript=transcript,
            mode="mock" if mock else "live",
            provider="mock" if mock else "meta",
            models=[] if mock else ([self.settings.meta_voice_model] if audio is not None else [])
            + [self.settings.meta_spark_model],
            stages=stages,
            notice="MOCK MODE — NOT A LIVE MODEL RESPONSE" if mock else None,
        )

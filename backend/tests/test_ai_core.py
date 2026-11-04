from dataclasses import replace
import io
import json
import wave

from fastapi.testclient import TestClient
import pytest
import requests
from pydantic import ValidationError

from app.api.v1.routes.analysis import get_pipeline
from app.core.config import get_settings
from app.main import app
from app.providers.meta.client import MetaClient, ProviderError
from app.providers.meta.muse_spark import MuseSpark
from app.providers.meta.voice_transcribe import MuseVoiceTranscribe
from app.schemas.analysis import MaintenanceAnalysis
from app.services.agent.mock import MockProvider
from app.services.agent.pipeline import AnalysisPipeline, PipelineError
from app.services.agent.safety import validate_safety


MOCK_SETTINGS = replace(get_settings(), demo_mock_mode=True)
LIVE_SETTINGS = replace(get_settings(), demo_mock_mode=False)
JPEG = b"\xff\xd8demo\xff\xd9"


def wav_sample() -> bytes:
    out = io.BytesIO()
    with wave.open(out, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(16000)
        writer.writeframes(b"\x00\x00" * 1600)
    return out.getvalue()


def valid_analysis() -> MaintenanceAnalysis:
    return MockProvider().analyze("Air conditioner not cooling.", None, None)


def test_schema_rejects_invalid_enum_and_review_flag():
    payload = valid_analysis().model_dump()
    payload["severity"] = "extreme"
    payload["requires_human_review"] = False
    with pytest.raises(ValidationError):
        MaintenanceAnalysis.model_validate(payload)


def test_schema_rejects_missing_and_extra_fields():
    payload = valid_analysis().model_dump()
    payload.pop("evidence")
    payload["unverified_history"] = "recent service"
    with pytest.raises(ValidationError):
        MaintenanceAnalysis.model_validate(payload)


def test_text_only_mock_pipeline_and_mode():
    result = AnalysisPipeline(MOCK_SETTINGS).run("AC is not cooling.")
    assert result.mode == "mock"
    assert result.provider == "mock"
    assert result.notice == "MOCK MODE — NOT A LIVE MODEL RESPONSE"
    assert result.stages[1].status == "skipped"
    assert result.analysis.requires_human_review
    assert not result.analysis.visual_observations


def test_image_input_shape_in_meta_adapter():
    class FakeClient:
        def post(self, path, *, payload):
            assert path == "/responses"
            assert payload["model"] == LIVE_SETTINGS.meta_spark_model
            content = payload["input"][1]["content"]
            assert content[1]["type"] == "input_image"
            assert content[1]["image_url"].startswith("data:image/jpeg;base64,")
            assert payload["text"]["format"]["type"] == "json_schema"
            assert payload["text"]["format"]["strict"] is True
            return {"status": "completed", "output": [
                {"type": "message", "content": [
                    {"type": "output_text", "text": valid_analysis().model_dump_json()}
                ]}
            ]}
    assert MuseSpark(FakeClient(), LIVE_SETTINGS).analyze("AC not cooling.", None, JPEG)


def test_invalid_model_json_is_visible_error():
    class FakeClient:
        def post(self, path, *, payload):
            return {"status": "completed", "output": [
                {"type": "message", "content": [{"type": "output_text", "text": "{bad"}]}
            ]}
    with pytest.raises(ProviderError, match="validated") as error:
        MuseSpark(FakeClient(), LIVE_SETTINGS).analyze("AC not cooling.", None, None)
    assert error.value.code == "MODEL_OUTPUT_INVALID"


def test_voice_adapter_multipart_shape():
    class FakeClient:
        @staticmethod
        def json_part(value):
            return (None, json.dumps(value), "application/json")

        def post(self, path, *, files):
            assert path == "/asr/transcribe"
            request = json.loads(files["request"][1])
            assert request == {"model": LIVE_SETTINGS.meta_voice_model,
                               "audioEncoding": "WAV", "mode": "PUSH_TO_TALK"}
            assert files["audio"][2] == "audio/wav"
            return {"transcript": "example", "sessionId": "session-test"}
    assert MuseVoiceTranscribe(FakeClient(), LIVE_SETTINGS).transcribe(wav_sample()) == "example"


class FakeResponse:
    def __init__(self, status=200, body=None):
        self.status_code = status
        self.ok = status < 400
        self.headers = {"x-request-id": "test-request"}
        self.body = body or {"ok": True}

    def json(self):
        return self.body


def test_meta_client_http_error(monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "unit-test-only")

    class Session:
        def post(self, *args, **kwargs):
            assert kwargs["headers"]["Authorization"] == "Bearer unit-test-only"
            return FakeResponse(400)
    with pytest.raises(ProviderError) as error:
        MetaClient(LIVE_SETTINGS, Session()).post("/responses", payload={"model": "test"})
    assert error.value.code == "PROVIDER_REJECTED"


def test_meta_client_timeout_bounded(monkeypatch):
    monkeypatch.setenv("MODEL_API_KEY", "unit-test-only")
    monkeypatch.setattr("app.providers.meta.client.time.sleep", lambda _: None)

    class Session:
        calls = 0

        def post(self, *args, **kwargs):
            self.calls += 1
            raise requests.Timeout()
    session = Session()
    with pytest.raises(ProviderError) as error:
        MetaClient(LIVE_SETTINGS, session).post("/responses", payload={"model": "test"})
    assert error.value.code == "PROVIDER_TIMEOUT"
    assert session.calls == 3


def test_safety_hazard_escalation_and_unsafe_rejection():
    analysis = validate_safety(valid_analysis(), "There is smoke by the AC.", None, False)
    assert analysis.suggested_priority == "urgent"
    assert analysis.safety_flags
    analysis.safe_checklist.append("Open the panel.")
    with pytest.raises(ProviderError) as error:
        validate_safety(analysis, "There is smoke by the AC.", None, False)
    assert error.value.code == "UNSAFE_MODEL_OUTPUT"


def test_still_image_cannot_support_audio_claim():
    analysis = valid_analysis()
    analysis.visual_observations = ["Rattling sound from the unit"]
    with pytest.raises(ProviderError) as error:
        validate_safety(analysis, "AC is not cooling.", None, True)
    assert error.value.code == "MODEL_OUTPUT_INVALID"


def test_mode_separation_and_audio_pipeline():
    class Analyzer:
        def analyze(self, description, transcript, image):
            assert transcript == "Verified test transcript"
            assert image == JPEG
            return valid_analysis()

    class Transcriber:
        def transcribe(self, audio):
            return "Verified test transcript"
    result = AnalysisPipeline(LIVE_SETTINGS, Analyzer(), Transcriber()).run(
        "AC not cooling.", JPEG, wav_sample()
    )
    assert result.mode == "live"
    assert result.provider == "meta"
    assert result.notice is None
    assert result.models == [LIVE_SETTINGS.meta_voice_model, LIVE_SETTINGS.meta_spark_model]


def test_provider_failure_never_falls_back():
    class FailingAnalyzer:
        def analyze(self, description, transcript, image):
            raise ProviderError("PROVIDER_UNAVAILABLE", "Meta API unavailable.", 503)
    with pytest.raises(PipelineError) as error:
        AnalysisPipeline(LIVE_SETTINGS, FailingAnalyzer()).run("AC not cooling.")
    assert error.value.code == "PROVIDER_UNAVAILABLE"
    assert error.value.stage == "analysis"


def test_route_mock_and_validation():
    app.dependency_overrides[get_pipeline] = lambda: AnalysisPipeline(MOCK_SETTINGS)
    try:
        with TestClient(app) as client:
            good = client.post("/api/v1/analysis", data={"description": "AC not cooling."})
            bad = client.post("/api/v1/analysis", data={"description": ""})
            invalid_audio = client.post(
                "/api/v1/analysis", data={"description": "AC not cooling."},
                files={"audio": ("bad.wav", b"bad", "audio/wav")},
            )
        assert good.status_code == 200
        assert good.json()["mode"] == "mock"
        assert good.json()["analysis"]["requires_human_review"] is True
        assert bad.status_code == 422
        assert bad.json()["error"]["code"] == "MISSING_REPORT"
        assert invalid_audio.status_code == 422
        assert invalid_audio.json()["error"]["code"] == "INVALID_AUDIO"
    finally:
        app.dependency_overrides.clear()

from dataclasses import replace
import io
from pathlib import Path
from uuid import UUID
import wave

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.api.v1.routes.analysis import get_pipeline
from app.api.v1.routes.work_orders import get_media_storage
from app.core.config import get_settings
from app.db.session import Base, get_db
from app.main import app
from app.models import AgentRun, MediaAsset, WorkOrder
from app.providers.meta.client import ProviderError
from app.services.agent.mock import MockProvider
from app.services.agent.pipeline import AnalysisPipeline
from app.services.work_order_service import WorkOrderService


def wav_sample() -> bytes:
    out = io.BytesIO()
    with wave.open(out, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(16000)
        writer.writeframes(b"\x00\x00" * 1600)
    return out.getvalue()


@pytest.fixture
def context(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    settings = replace(get_settings(), demo_mock_mode=True, upload_dir=tmp_path / "uploads")

    def test_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = test_db
    app.dependency_overrides[get_pipeline] = lambda: AnalysisPipeline(settings)
    from app.storage.local_storage import LocalMediaStorage
    app.dependency_overrides[get_media_storage] = lambda: LocalMediaStorage(settings)
    with TestClient(app) as client:
        yield client, engine, settings
    app.dependency_overrides.clear()
    engine.dispose()


def create_order(client, **kwargs):
    return client.post("/api/v1/intakes/analyze", data={"description": "AC not cooling in Meeting Room 3."}, **kwargs)


def test_create_from_analysis_and_relationships(context):
    client, engine, _ = context
    response = create_order(client)
    assert response.status_code == 200, response.text
    body = response.json()
    order = body["work_order"]
    assert UUID(order["id"])
    assert order["status"] == "draft"
    assert order["requires_human_review"] is True
    assert order["evidence"][0]["source"] == "user_text"
    assert body["agent_run"]["status"] == "succeeded"
    assert body["mode"] == "mock"
    with Session(engine) as session:
        saved = session.get(WorkOrder, order["id"])
        assert saved.agent_run.status == "succeeded"
        assert any(e.event_type == "work_order_created" for e in saved.agent_run.events)
        assert saved.created_at.tzinfo is not None
        assert saved.updated_at.tzinfo is not None


def test_media_storage_and_api_path_hiding(context):
    client, engine, settings = context
    response = create_order(client, files={
        "image": ("../unsafe name.jpg", b"\xff\xd8test\xff\xd9", "image/jpeg"),
        "audio": ("voice.wav", wav_sample(), "audio/wav"),
    })
    assert response.status_code == 200, response.text
    order_id = response.json()["work_order"]["id"]
    detail = client.get(f"/api/v1/work-orders/{order_id}").json()
    assert len(detail["media_assets"]) == 2
    assert "storage_path" not in detail["media_assets"][0]
    assert "storage_path" not in response.text
    for asset in detail["media_assets"]:
        media = client.get(f"/api/v1/work-orders/{order_id}/media/{asset['id']}")
        assert media.status_code == 200
        assert media.headers["content-type"].startswith(asset["mime_type"])
        assert media.headers["x-content-type-options"] == "nosniff"
    assert client.get(f"/api/v1/work-orders/{'0'*8}-0000-0000-0000-000000000000/media/{detail['media_assets'][0]['id']}").status_code == 404
    first_asset_id = detail["media_assets"][0]["id"]
    with Session(engine) as session:
        asset = session.get(MediaAsset, first_asset_id)
        original_path = asset.storage_path
        asset.storage_path = str(settings.upload_dir.parent / "outside.jpg")
        session.commit()
    assert client.get(f"/api/v1/work-orders/{order_id}/media/{first_asset_id}").status_code == 404
    with Session(engine) as session:
        asset = session.get(MediaAsset, first_asset_id)
        asset.storage_path = original_path
        session.commit()
    with Session(engine) as session:
        assets = session.scalars(select(MediaAsset)).all()
        assert len(assets) == 2
        assert all(Path(asset.storage_path).is_file() for asset in assets)
        assert all(Path(asset.storage_path).parent == settings.upload_dir for asset in assets)
        assert all(UUID(Path(asset.storage_path).stem) for asset in assets)
        assert all("/" not in asset.original_filename for asset in assets)
        assert all(asset.created_at.tzinfo is not None for asset in assets)


def test_invalid_media_rejected_and_failed_run_persists(context):
    client, engine, settings = context
    response = create_order(client, files={"image": ("bad.png", b"not-an-image", "image/png")})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_IMAGE"
    run_id = response.json()["error"]["agent_run_id"]
    with Session(engine) as session:
        run = session.get(AgentRun, run_id)
        assert run.status == "failed"
        assert run.error_code == "INVALID_IMAGE"
        assert run.completed_at.tzinfo is not None
        assert any(e.event_type == "processing_failed" for e in run.events)
        assert session.scalar(select(func.count()).select_from(WorkOrder)) == 0
    assert not settings.upload_dir.exists() or not list(settings.upload_dir.iterdir())


def test_second_upload_failure_cleans_first_file(context):
    client, engine, settings = context
    response = create_order(client, files={
        "image": ("unit.jpg", b"\xff\xd8test\xff\xd9", "image/jpeg"),
        "audio": ("bad.mp3", b"not-a-wav", "audio/mpeg"),
    })
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_AUDIO"
    assert not list(settings.upload_dir.iterdir())
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(MediaAsset)) == 0
        assert session.get(AgentRun, response.json()["error"]["agent_run_id"]).status == "failed"


def test_list_detail_edit_approve_and_transitions(context):
    client, engine, _ = context
    first = create_order(client).json()["work_order"]["id"]
    second = create_order(client).json()["work_order"]["id"]
    listed = client.get("/api/v1/work-orders", params={"limit": 1, "offset": 0}).json()
    assert listed["total"] == 2
    assert len(listed["items"]) == 1
    assert client.get("/api/v1/work-orders", params={"status": "approved"}).json()["total"] == 0
    assert client.get(f"/api/v1/work-orders/{first}").status_code == 200
    assert client.get("/api/v1/work-orders/not-a-uuid").status_code == 422
    assert client.get(f"/api/v1/work-orders/{'0' * 8}-0000-0000-0000-000000000000").status_code == 404

    edited = client.patch(f"/api/v1/work-orders/{first}", json={
        "title": "Meeting Room 3 AC inspection",
        "suggested_priority": "high",
        "priority_reason": "Room unavailable; coordinator review needed.",
    })
    assert edited.status_code == 200
    assert edited.json()["work_order"]["title"] == "Meeting Room 3 AC inspection"
    assert client.patch(f"/api/v1/work-orders/{first}", json={"safe_checklist": ["Open the panel."]}).status_code == 422
    assert client.patch(f"/api/v1/work-orders/{first}", json={"technician_message_draft": "Touch the wiring."}).status_code == 422
    assert client.patch(f"/api/v1/work-orders/{first}", json={"safe_checklist": ["  "]}).status_code == 422
    approved = client.post(f"/api/v1/work-orders/{first}/approve")
    assert approved.status_code == 200
    assert approved.json()["work_order"]["status"] == "approved"
    assert approved.json()["work_order"]["approved_at"] is not None
    assert any(e["event_type"] == "work_order_approved" for e in approved.json()["events"])
    assert client.post(f"/api/v1/work-orders/{first}/approve").status_code == 409
    assert client.patch(f"/api/v1/work-orders/{first}", json={"title": "Late edit"}).status_code == 409
    assert client.patch(f"/api/v1/work-orders/{first}/status", json={"status": "completed"}).status_code == 409
    assert client.patch(f"/api/v1/work-orders/{first}/status", json={"status": "in_progress"}).status_code == 200
    assert client.patch(f"/api/v1/work-orders/{first}/status", json={"status": "completed"}).status_code == 200
    assert client.patch(f"/api/v1/work-orders/{first}/status", json={"status": "cancelled"}).status_code == 409
    assert client.patch(f"/api/v1/work-orders/{second}/status", json={"status": "cancelled"}).status_code == 200
    assert client.get("/api/v1/work-orders", params={"status": "approved"}).json()["total"] == 0
    with Session(engine) as session:
        order = session.get(WorkOrder, first)
        assert order.approved_at.tzinfo is not None
        assert order.status == "completed"
        assert any(e.event_type == "status_changed" for e in order.agent_run.events)


def test_live_mode_uses_injected_provider_without_paid_call(context):
    client, engine, settings = context

    class Analyzer:
        def analyze(self, description, transcript, image):
            return MockProvider().analyze(description, transcript, image)

    live = replace(settings, demo_mock_mode=False)
    app.dependency_overrides[get_pipeline] = lambda: AnalysisPipeline(live, Analyzer())
    response = create_order(client)
    assert response.status_code == 200, response.text
    assert response.json()["mode"] == "live"
    assert response.json()["agent_run"]["provider"] == "meta"
    with Session(engine) as session:
        run = session.get(AgentRun, response.json()["agent_run"]["id"])
        assert run.provider == "meta"
        assert run.models == [live.meta_spark_model]


def test_pipeline_failure_cleans_media_and_keeps_failed_run(context):
    client, engine, settings = context

    class FailingAnalyzer:
        def analyze(self, description, transcript, image):
            raise ProviderError("PROVIDER_UNAVAILABLE", "Meta API unavailable.", 503)

    live = replace(settings, demo_mock_mode=False)
    app.dependency_overrides[get_pipeline] = lambda: AnalysisPipeline(live, FailingAnalyzer())
    response = create_order(client, files={"image": ("unit.jpg", b"\xff\xd8test\xff\xd9", "image/jpeg")})
    assert response.status_code == 503
    assert response.json()["error"]["mode"] == "live"
    assert response.json()["error"]["code"] == "PROVIDER_UNAVAILABLE"
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(WorkOrder)) == 0
        assert session.scalar(select(func.count()).select_from(MediaAsset)) == 0
        run = session.get(AgentRun, response.json()["error"]["agent_run_id"])
        assert run.status == "failed"
        assert run.error_code == "PROVIDER_UNAVAILABLE"
    assert not list(settings.upload_dir.iterdir())


def test_transaction_failure_rolls_back_order_and_cleans_media(context, monkeypatch):
    client, engine, settings = context

    def broken_mapping(*args, **kwargs):
        raise RuntimeError("injected test failure")

    monkeypatch.setattr(WorkOrderService, "from_analysis", broken_mapping)
    response = create_order(client, files={"image": ("unit.jpg", b"\xff\xd8test\xff\xd9", "image/jpeg")})
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "PROCESSING_FAILED"
    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(WorkOrder)) == 0
        assert session.scalar(select(func.count()).select_from(MediaAsset)) == 0
        assert session.get(AgentRun, response.json()["error"]["agent_run_id"]).status == "failed"
    assert not list(settings.upload_dir.iterdir())


def test_persistence_after_new_engine(context):
    client, engine, _ = context
    order_id = create_order(client).json()["work_order"]["id"]
    other_engine = create_engine(engine.url, connect_args={"check_same_thread": False})
    try:
        with Session(other_engine) as session:
            assert session.get(WorkOrder, order_id).status == "draft"
    finally:
        other_engine.dispose()

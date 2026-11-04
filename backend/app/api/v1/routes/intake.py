from time import monotonic

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.db.session import get_db
from app.models import AgentRun, MediaAsset
from app.models.entities import utc_now
from app.schemas.work_order import AgentRunRead, IntakeResult, WorkOrderRead
from app.services.agent.pipeline import AnalysisPipeline, PipelineError
from app.services.work_order_service import WorkOrderService, event
from app.storage.local_storage import LocalMediaStorage, StoredMedia
from app.api.v1.routes.analysis import get_pipeline

router = APIRouter(prefix="/api/v1")


@router.post("/intakes/analyze", response_model=IntakeResult)
async def intake_analyze(
    description: str = Form(""),
    image: UploadFile | None = File(None),
    audio: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    pipeline: AnalysisPipeline = Depends(get_pipeline),
) -> IntakeResult | JSONResponse:
    started = monotonic()
    mock = pipeline.settings.demo_mock_mode
    run = AgentRun(status="running", provider="mock" if mock else "meta", models=[])
    db.add(run)
    db.add(event(run, "intake_created", "intake", "succeeded", "Intake received."))
    db.commit()
    storage = LocalMediaStorage(pipeline.settings)
    saved: list[StoredMedia] = []
    try:
        image_bytes = await image.read(pipeline.settings.max_image_mb * 1024 * 1024 + 1) if image else None
        audio_bytes = await audio.read(pipeline.settings.max_audio_mb * 1024 * 1024 + 1) if audio else None
        if image is not None:
            saved.append(storage.save("image", image.filename, image.content_type, image_bytes))
        if audio is not None:
            saved.append(storage.save("audio", audio.filename, audio.content_type, audio_bytes))
        result = await run_in_threadpool(pipeline.run, description, image_bytes, audio_bytes)
        order = WorkOrderService.from_analysis(result, run)
        db.add(order)
        db.flush()
        for item in saved:
            db.add(MediaAsset(
                work_order=order, kind=item.kind, original_filename=item.original_filename,
                mime_type=item.mime_type, size_bytes=item.size_bytes,
                storage_path=str(item.storage_path),
            ))
        for stage in result.stages:
            db.add(event(run, f"{stage.name}_{stage.status}", stage.name, stage.status,
                         f"{stage.name.capitalize()} {stage.status}."))
        db.add(event(run, "work_order_created", "work_order", "succeeded", "Draft work order created."))
        run.status = "succeeded"
        run.models = result.models
        run.completed_at = utc_now()
        run.duration_ms = int((monotonic() - started) * 1000)
        db.commit()
        db.refresh(order)
        db.refresh(run)
        return IntakeResult(
            work_order=WorkOrderRead.model_validate(order),
            agent_run=AgentRunRead.model_validate(run),
            mode=result.mode,
            notice=result.notice,
            stages=[stage.model_dump() for stage in result.stages],
        )
    except Exception as exc:
        db.rollback()
        storage.cleanup(saved)
        failure = exc if isinstance(exc, PipelineError) else PipelineError(
            "PROCESSING_FAILED", "Intake could not be completed. Please retry.", "work_order", 500
        )
        failed_run = db.get(AgentRun, run.id)
        if failed_run is not None:
            failed_run.status = "failed"
            failed_run.completed_at = utc_now()
            failed_run.duration_ms = int((monotonic() - started) * 1000)
            failed_run.error_code = failure.code
            failed_run.error_message_safe = failure.message
            db.add(event(failed_run, "processing_failed", failure.stage, "failed",
                         f"Processing failed at {failure.stage}."))
            db.commit()
        return JSONResponse(
            status_code=failure.status_code,
            content={"error": {"code": failure.code, "message": failure.message,
                               "stage": failure.stage, "mode": "mock" if mock else "live",
                               "agent_run_id": run.id}},
        )

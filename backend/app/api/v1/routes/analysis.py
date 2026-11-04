from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.schemas.analysis import AnalysisResponse
from app.services.agent.pipeline import AnalysisPipeline, PipelineError

router = APIRouter(prefix="/api/v1")


def get_pipeline() -> AnalysisPipeline:
    return AnalysisPipeline()


@router.post("/analysis", response_model=AnalysisResponse)
async def analyze(
    description: str = Form(""),
    image: UploadFile | None = File(None),
    audio: UploadFile | None = File(None),
    pipeline: AnalysisPipeline = Depends(get_pipeline),
) -> AnalysisResponse | JSONResponse:
    settings = get_settings()
    image_bytes = await image.read(settings.max_image_mb * 1024 * 1024 + 1) if image else None
    audio_bytes = await audio.read(settings.max_audio_mb * 1024 * 1024 + 1) if audio else None
    try:
        return await run_in_threadpool(pipeline.run, description, image_bytes, audio_bytes)
    except PipelineError as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message, "stage": exc.stage,
                               "mode": "mock" if pipeline.settings.demo_mock_mode else "live"}},
        )

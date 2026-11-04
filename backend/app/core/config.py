from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent
WORKSPACE_DIR = PROJECT_DIR.parent

# Prefer a backend-specific file; the workspace-root file also supports the
# current local handoff. Environment variables take precedence over both.
for env_path in (BACKEND_DIR / ".env", PROJECT_DIR / ".env", WORKSPACE_DIR / ".env"):
    if env_path.is_file():
        load_dotenv(env_path, override=False)
        break


@dataclass(frozen=True)
class Settings:
    database_url: str
    cors_origins: tuple[str, ...]
    demo_mock_mode: bool
    meta_key_configured: bool
    meta_api_base_url: str
    meta_spark_model: str
    meta_voice_model: str
    request_timeout_seconds: int
    max_image_mb: int
    max_audio_mb: int
    upload_dir: Path


@lru_cache
def get_settings() -> Settings:
    raw_mode = os.getenv("DEMO_MOCK_MODE", "false").strip().lower()
    if raw_mode not in {"true", "false"}:
        raise ValueError("DEMO_MOCK_MODE must be true or false")
    base_url = os.getenv("META_API_BASE_URL", "https://api.meta.ai/v1").rstrip("/")
    # A local handoff may contain the full Responses URL rather than the API
    # base. Normalize this one documented route to avoid /responses/responses.
    if base_url.endswith("/v1/responses"):
        base_url = base_url.removesuffix("/responses")
    if not base_url.endswith("/v1"):
        raise ValueError("META_API_BASE_URL must end with /v1")
    upload_dir = (PROJECT_DIR / os.getenv("UPLOAD_DIR", ".uploads")).resolve()
    if not upload_dir.is_relative_to(PROJECT_DIR.resolve()):
        raise ValueError("UPLOAD_DIR must be within the project directory")
    return Settings(
        database_url=os.getenv("DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'fieldops.db'}"),
        cors_origins=tuple(
            origin.strip()
            for origin in os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000").split(",")
            if origin.strip()
        ),
        demo_mock_mode=raw_mode == "true",
        meta_key_configured=bool(os.getenv("MODEL_API_KEY")),
        meta_api_base_url=base_url,
        meta_spark_model=os.getenv("META_SPARK_MODEL", "muse-spark-1.3"),
        meta_voice_model=os.getenv("META_VOICE_MODEL", "muse-voice-transcribe-1.0"),
        request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "60")),
        max_image_mb=int(os.getenv("MAX_IMAGE_MB", "10")),
        max_audio_mb=int(os.getenv("MAX_AUDIO_MB", "20")),
        upload_dir=upload_dir,
    )

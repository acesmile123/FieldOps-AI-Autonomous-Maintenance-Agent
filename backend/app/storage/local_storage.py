from dataclasses import dataclass
from pathlib import Path
import re
from uuid import uuid4

from app.core.config import Settings
from app.services.agent.pipeline import PipelineError, validate_audio, validate_image


@dataclass(frozen=True)
class StoredMedia:
    kind: str
    original_filename: str
    mime_type: str
    size_bytes: int
    storage_path: Path


class LocalMediaStorage:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.directory = settings.upload_dir

    def save(self, kind: str, filename: str | None, mime: str | None, content: bytes) -> StoredMedia:
        name = Path((filename or "").replace("\\", "/")).name
        name = re.sub(r"[^A-Za-z0-9._-]", "_", name)[:200]
        if not name or name in {".", ".."}:
            raise PipelineError("INVALID_FILE", "Provide a valid upload filename.", "validation")
        ext = Path(name).suffix.lower()
        if kind == "image":
            if ext not in {".jpg", ".jpeg"} or mime != "image/jpeg":
                raise PipelineError("INVALID_IMAGE", "Upload a JPEG file with image/jpeg type.", "validation")
            validate_image(content, self.settings)
            suffix, canonical_mime = ".jpg", "image/jpeg"
        elif kind == "audio":
            if ext != ".wav" or mime not in {"audio/wav", "audio/x-wav", "audio/wave"}:
                raise PipelineError("INVALID_AUDIO", "Upload a WAV file with audio/wav type.", "validation")
            validate_audio(content, self.settings)
            suffix, canonical_mime = ".wav", "audio/wav"
        else:
            raise PipelineError("INVALID_FILE", "Unsupported upload kind.", "validation")
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f"{uuid4()}{suffix}"
        with path.open("xb") as handle:
            handle.write(content)
        return StoredMedia(kind, name, canonical_mime, len(content), path)

    @staticmethod
    def cleanup(items: list[StoredMedia]) -> None:
        for item in items:
            item.storage_path.unlink(missing_ok=True)

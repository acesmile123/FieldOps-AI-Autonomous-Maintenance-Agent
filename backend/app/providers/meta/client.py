import json
import logging
import os
import time
from typing import Any

import requests

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)
TRANSIENT_STATUSES = {429, 500, 502, 503, 504}


class ProviderError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 502):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class MetaClient:
    def __init__(self, settings: Settings | None = None, session: requests.Session | None = None):
        self.settings = settings or get_settings()
        self.session = session or requests.Session()

    def post(self, path: str, *, payload: dict[str, Any] | None = None,
             files: dict[str, Any] | None = None) -> dict[str, Any]:
        key = os.getenv("MODEL_API_KEY")
        if not key:
            raise ProviderError("META_KEY_MISSING", "Meta API key is not configured.", 503)
        headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        url = f"{self.settings.meta_api_base_url}{path}"
        for attempt in range(3):
            started = time.monotonic()
            try:
                response = self.session.post(
                    url, headers=headers,
                    json=payload,
                    files=files,
                    timeout=self.settings.request_timeout_seconds,
                )
            except requests.Timeout:
                if attempt < 2:
                    time.sleep(0.25 * (2 ** attempt))
                    continue
                raise ProviderError("PROVIDER_TIMEOUT", "Meta API timed out. Please retry.", 504) from None
            except requests.RequestException:
                raise ProviderError("PROVIDER_UNAVAILABLE", "Meta API is unavailable. Please retry.", 503) from None
            logger.info("Meta request path=%s status=%s request_id=%s latency_ms=%d",
                        path, response.status_code, response.headers.get("x-request-id", "unknown"),
                        int((time.monotonic() - started) * 1000))
            if response.status_code in TRANSIENT_STATUSES and attempt < 2:
                time.sleep(0.25 * (2 ** attempt))
                continue
            if not response.ok:
                code = "PROVIDER_RATE_LIMITED" if response.status_code == 429 else "PROVIDER_REJECTED"
                raise ProviderError(code, "Meta API could not process the request. Please retry or check your input.",
                                    429 if response.status_code == 429 else 502)
            try:
                body = response.json()
            except ValueError:
                raise ProviderError("PROVIDER_BAD_RESPONSE", "Meta API returned an unreadable response.") from None
            if not isinstance(body, dict):
                raise ProviderError("PROVIDER_BAD_RESPONSE", "Meta API returned an unexpected response.")
            return body
        raise ProviderError("PROVIDER_UNAVAILABLE", "Meta API is unavailable. Please retry.")

    @staticmethod
    def json_part(value: dict[str, Any]) -> tuple[None, str, str]:
        return (None, json.dumps(value), "application/json")

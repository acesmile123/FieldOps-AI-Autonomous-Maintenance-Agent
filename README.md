# FieldOps AI

FieldOps AI is a maintenance intake and human-reviewed work-order assistant for the Meta Global AI Developer Hackathon.

**Release candidate:** Local single-workspace MVP. The application accepts intake, creates a persistent draft, shows original evidence and audit events, and supports human edits and explicit approval. It has no authentication and must not be exposed as a public multi-user service.

## Requirements

- Python 3.11+ and Node.js 20.9+ (verified with Python 3.13.1 and Node.js 24.11.1)
- npm
- A Meta Model API key for live model calls; mock rehearsal needs no key

## Backend

Run these commands from `fieldops_ai_codex_handoff` in PowerShell. First copy `.env.example` to `backend/.env` for an isolated local setup. It starts in visibly labelled mock mode; leave `MODEL_API_KEY` blank for rehearsal.

```powershell
Copy-Item .env.example backend/.env
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
cd backend
..\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000/health`. The backend initializes `backend/fieldops.db` with `work_orders`, `media_assets`, `agent_runs`, and `agent_events` tables. Timestamps are stored as UTC values with timezone information.

For live Meta configuration, set `MODEL_API_KEY` in the ignored `backend/.env` and change `DEMO_MOCK_MODE=false`, then restart the backend. The backend also reads a project-root or parent-workspace `.env` if no closer file exists. Environment variables override file values. Never put the key in `frontend/.env.local` or any `NEXT_PUBLIC_` variable. With `DEMO_MOCK_MODE=true`, intake and analysis return deterministic mock data explicitly marked `mode=mock`; neither endpoint silently falls back to mock after a live error.

## Frontend

In a second terminal, run:

```powershell
cd fieldops_ai_codex_handoff\frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The browser calls `http://localhost:8000` by default. If the backend uses another origin, set `NEXT_PUBLIC_API_BASE_URL` in an ignored `frontend/.env.local` and set `BACKEND_CORS_ORIGINS` on the backend to the frontend origin. Restart Next.js after changing this variable.

Browser routes:

| Route | Purpose |
| --- | --- |
| `/` | Overview and recent work orders |
| `/intake` | Description, JPEG and WAV intake with file previews and validation |
| `/work-orders` | Status-filtered, paginated work-order queue |
| `/work-orders/{id}` | Evidence, reasoning, draft edits, approval and audit timeline |

The sidebar shows backend connection and live/mock mode from `/health`. Each work order displays its actual agent-run provider. `DEMO_MOCK_MODE=true` uses labelled mock results; `DEMO_MOCK_MODE=false` calls Meta with the backend-only key. Stop and restart the backend after changing mode. A failed live request does not switch to mock.

## M2 analysis endpoint

`POST /api/v1/analysis` accepts multipart form data: `description` (text), `image` (optional JPEG), and `audio` (optional mono 16-bit PCM WAV at 16 or 24 kHz). Provide description or audio. The application limits images to 10 MB and audio to 20 MB by default; Meta's Voice endpoint also limits audio to 10 minutes and a 32 MB total request body.

The response contains `analysis` (validated `MaintenanceAnalysis`), `transcript` when audio is present, `mode` (`live` or `mock`), `provider`, `models`, `stages`, and `notice`. Errors use `{"error":{"code":"...","message":"...","stage":"...","mode":"..."}}`. Attachments are read into memory for the request and are not saved in M2. A failed audio or image step returns an error; it is never silently omitted.

Example text-only request in PowerShell:

```powershell
curl.exe -X POST http://localhost:8000/api/v1/analysis -F "description=The AC in Meeting Room 3 is not cooling."
```

For files, add `-F "image=@path/to/photo.jpg;type=image/jpeg"` and/or `-F "audio=@path/to/voice.wav;type=audio/wav"`. Set `DEMO_MOCK_MODE=false` and restart the backend for live endpoint calls.

## M3 intake and work orders

`POST /api/v1/intakes/analyze` accepts the same multipart fields as `/api/v1/analysis`. It calls the existing M2 pipeline once, stores a `draft` work order, media metadata and agent events, and returns:

```json
{
  "work_order": { "id": "uuid", "status": "draft", "requires_human_review": true },
  "agent_run": { "id": "uuid", "status": "succeeded", "provider": "meta" },
  "mode": "live",
  "notice": null,
  "stages": []
}
```

The objects contain additional analysis and run fields. On failure, the response contains `error.code`, a safe `error.message`, `error.stage`, `error.mode`, and `error.agent_run_id`. Failed runs and a failure event remain in SQLite.

Work-order routes:

| Route | Purpose |
| --- | --- |
| `GET /api/v1/work-orders?status=draft&limit=20&offset=0` | Newest-first list with total count |
| `GET /api/v1/work-orders/{id}` | Full work order, media metadata, agent-run summary and events |
| `GET /api/v1/work-orders/{id}/media/{asset_id}` | Original JPEG or WAV for that work order, by asset ID |
| `PATCH /api/v1/work-orders/{id}` | Edit allowed fields while draft |
| `POST /api/v1/work-orders/{id}/approve` | Explicitly approve a draft and record the event |
| `PATCH /api/v1/work-orders/{id}/status` | Valid lifecycle transitions only |

`PATCH /status` accepts `{"status":"in_progress"}`, `{"status":"completed"}`, or `{"status":"cancelled"}` where allowed. Invalid transitions return HTTP 409. Approval and status changes never send messages or dispatch technicians.

Uploaded JPEG/WAV files are validated by MIME, extension, size and the M2 content checks. Files use generated UUID names under the ignored project `.uploads/`; database metadata keeps sanitized original names. The media route verifies work-order ownership and resolves the file under the upload directory. The API never returns local storage paths. Files from a failed intake are removed. This local single-workspace demo has no authentication; do not expose it as a public multi-user service.

## Checks

```powershell
cd fieldops_ai_codex_handoff\backend
..\.venv\Scripts\python -m pytest tests -q -p no:cacheprovider --basetemp=.test-tmp
..\.venv\Scripts\python -m compileall -q app

cd ..\frontend
npm run lint
npm run typecheck
npm run build
```

## Browser demo flow

Open `/intake`; submit a text report, optional JPEG equipment photo and optional mono PCM WAV voice note. The browser creates a draft and opens its review page. Inspect the original media, transcript, source-labelled claims, uncertainty, safe checklist and audit history. Edit the draft, save, then explicitly confirm approval. Refresh to verify persistence and use `/work-orders` to filter by status. The browser shows confirmed processing stages only after the synchronous intake endpoint responds. See [product specification](docs/PRODUCT_SPEC.md) and [build status](docs/BUILD_STATUS.md).

For a **paid live browser check**, first confirm accepted hackathon participation and available Meta credits in your account. Set the backend-only key and mode as above. Confirm `http://localhost:8000/health` reports `demo_mock_mode=false` and `meta_key_configured=true`, and that the browser header says `LIVE META`. Then submit one description with a rights-cleared JPEG and mono 16-bit PCM WAV (16 or 24 kHz). Confirm the resulting order shows a Meta provider, transcript, image evidence and audit stages. A provider failure must be shown as an error; do not describe a mock retry as a live result. No paid live request was made during M5 without authorization.

The current local SQLite file contains mock smoke-test records. For a clean recording, keep it intact and start the backend from `backend/` with a separate ignored database: `$env:DATABASE_URL='sqlite:///./demo_fieldops.db'`. The app creates its tables on startup. If you later choose to remove old data, first back up `backend/fieldops.db` and the project `.uploads/` directory; both are excluded from Git.

See [demo script](docs/DEMO_SCRIPT.md) and [submission checklist](docs/SUBMISSION_CHECKLIST.md) for release steps and remaining manual checks.

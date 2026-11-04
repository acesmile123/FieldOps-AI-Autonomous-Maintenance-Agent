# Technical Design --- FieldOps AI

**Status:** MVP implementation blueprint

------------------------------------------------------------------------

## 1. Architecture overview

Use a **modular monolith**:

-   Next.js frontend for intake, progress and review.
-   FastAPI backend for validation, orchestration, persistence and
    provider calls.
-   SQLite for work orders and audit events.
-   Meta Model API accessed only from the backend.
-   Local temporary storage for uploaded files during the hackathon
    demo.

``` text
Browser (Next.js)
  |
  | HTTPS / multipart upload / JSON
  v
FastAPI
  |
  +-- Intake Router
  |     +-- File validation
  |     +-- Temporary media storage
  |
  +-- Application / Agent Orchestrator
  |     +-- Voice transcription step
  |     +-- Multimodal issue extraction
  |     +-- Safe plan generation
  |     +-- Pydantic validation
  |     +-- Human approval state transition
  |
  +-- Provider adapters
  |     +-- Meta Voice Transcribe adapter
  |     +-- Meta Muse Spark adapter
  |     +-- Optional SAM 3.1 adapter
  |
  +-- SQLAlchemy repositories
        +-- Work orders
        +-- Media assets
        +-- Agent runs/events
        |
        v
      SQLite
```

## 2. Suggested repository structure

``` text
fieldops-ai/
├── AGENTS.md
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml                 # optional; only if useful
├── backend/
│   ├── pyproject.toml                 # or requirements.txt; choose one
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── logging.py
│   │   │   └── security.py
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── router.py
│   │   │       └── routes/
│   │   │           ├── health.py
│   │   │           ├── intake.py
│   │   │           └── work_orders.py
│   │   ├── schemas/
│   │   │   ├── intake.py
│   │   │   ├── work_order.py
│   │   │   └── agent.py
│   │   ├── models/
│   │   │   ├── work_order.py
│   │   │   ├── media_asset.py
│   │   │   ├── agent_run.py
│   │   │   └── agent_event.py
│   │   ├── repositories/
│   │   │   └── work_order_repository.py
│   │   ├── services/
│   │   │   ├── intake_service.py
│   │   │   ├── work_order_service.py
│   │   │   └── agent/
│   │   │       ├── orchestrator.py
│   │   │       ├── pipeline.py
│   │   │       ├── prompts.py
│   │   │       ├── validators.py
│   │   │       └── safety.py
│   │   ├── providers/
│   │   │   └── meta/
│   │   │       ├── client.py
│   │   │       ├── voice_transcribe.py
│   │   │       ├── muse_spark.py
│   │   │       └── sam.py              # optional
│   │   ├── storage/
│   │   │   └── local_storage.py
│   │   └── db/
│   │       ├── session.py
│   │       └── init_db.py
│   └── tests/
│       ├── test_health.py
│       ├── test_schemas.py
│       ├── test_pipeline.py
│       ├── test_work_order_state.py
│       └── test_api_intake.py
├── frontend/
│   ├── package.json
│   ├── next.config.ts
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx
│   │   │   ├── layout.tsx
│   │   │   └── work-orders/
│   │   │       ├── page.tsx
│   │   │       └── [id]/page.tsx
│   │   ├── components/
│   │   │   ├── intake-form.tsx
│   │   │   ├── upload-field.tsx
│   │   │   ├── processing-steps.tsx
│   │   │   ├── evidence-panel.tsx
│   │   │   ├── work-order-review.tsx
│   │   │   └── status-badge.tsx
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   ├── types.ts
│   │   │   └── utils.ts
│   │   └── styles/
│   └── public/
├── docs/
│   ├── PRODUCT_SPEC.md
│   ├── TECHNICAL_DESIGN.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── BUILD_STATUS.md
└── sample-data/
    └── README.md                       # instructions; do not add copyrighted/private data
```

Codex may simplify this structure if the deadline demands it, but
provider calls, orchestration, schemas and API routes must remain
separated.

## 3. Meta model/API integration plan

### 3.1 Provider configuration

Use backend-only environment variables: - `MODEL_API_KEY` --- Meta API
bearer key, matching the official quickstart naming. -
`META_API_BASE_URL=https://api.meta.ai/v1` -
`META_SPARK_MODEL=muse-spark-1.3` -
`META_VOICE_MODEL=muse-voice-transcribe-1.0` -
`META_SAM_MODEL=sam-3.1` - `DEMO_MOCK_MODE=true|false`

Model IDs and base URL must be configurable. Never hard-code
credentials.

### 3.2 Muse Voice Transcribe

Purpose: convert an uploaded voice recording into transcript text.

Official documentation currently describes: - Model ID:
`muse-voice-transcribe-1.0` - File transcription:
`POST /v1/asr/transcribe` - Realtime endpoint exists, but realtime
streaming is out of MVP scope.

Implementation: 1. Validate file size/type. 2. Send the file using the
exact request format from current Meta docs. 3. Parse transcript and any
returned turn metadata. 4. Save transcript text and provider request
metadata. 5. Display transcript to the user for correction.

Do not assume supported codecs, sample rates or maximum file duration.
Verify current docs and enforce only documented constraints.

### 3.3 Muse Spark

Purpose: - Interpret the text report and transcript. - Understand the
attached image if supported by the selected verified API format. -
Extract facts, unknowns and assumptions. - Draft a structured work order
and safe checklist.

Official documentation currently lists Muse Spark model IDs including: -
`muse-spark-1.3` - `muse-spark-1.2` - `muse-spark-1.1`

Use the current recommended model and exact Responses API / Chat
Completions / Messages schema from official docs. Structured output may
be used if the selected endpoint supports the required schema.

Prompt requirements: - Do not diagnose a mechanical/electrical fault as
fact. - Label the source of each claim: user report, transcript, visual
observation or inference. - Never invent equipment IDs, addresses,
dates, part numbers or repair history. - Return `unknown` or `null` when
unsupported. - Produce safe, non-invasive checklist items only. - Always
set `requires_human_review=true`.

### 3.4 SAM 3.1 (stretch)

Purpose: segment/outline a named object in a photo, such as
"air-conditioning unit".

Official docs describe `sam-3.1` as returning boxes and masks for
prompted objects, through the Responses API; files may be uploaded
through the Files API.

Important: - SAM is a segmentation model, not a fault diagnosis model. -
Use it only if the core MVP works and docs/API are verified. - Display
mask/box as a visual aid; do not interpret the mask as evidence of
equipment damage. - If SAM integration threatens the deadline, omit it
and document it as future work.

### 3.5 Provider abstraction

Create a small interface so the application is not coupled to
SDK-specific details:

-   `transcribe_audio(file) -> TranscriptionResult`
-   `analyze_maintenance_case(text, transcript, image) -> MaintenanceAnalysis`
-   `segment_image(image, prompt) -> SegmentationResult` (optional)

The adapter must: - Set timeouts. - Handle non-2xx responses. -
Normalize provider errors. - Retry only transient errors, with a small
bounded retry count. - Never retry invalid requests indefinitely. - Log
request ID/model/latency/status, not secrets or full sensitive payloads.

## 4. AI pipeline

### Pipeline stages

``` text
START
  |
  v
Validate intake and attachments
  |
  +-- invalid --> return actionable validation error
  |
  v
Create AgentRun(status=running)
  |
  v
Audio attached?
  | yes                         | no
  v                             v
Muse Voice Transcribe        Keep user text
  |                             |
  +--------------+--------------+
                 |
                 v
      Build normalized case context
                 |
                 v
      Muse Spark multimodal analysis
      (text + transcript + image if supported)
                 |
                 v
      Parse and validate structured output
                 |
          valid? | no
            yes  | bounded retry / fail
             |   |
             v   v
       Safety policy checks
             |
             v
       Persist draft work order
             |
             v
       Display evidence + unknowns
             |
             v
       Human edits / approves
             |
             v
       status = approved
             |
             v
            END
```

### Required separation of information

The model output and UI must distinguish:

-   **Reported:** directly stated by the user or transcript.
-   **Observed:** directly visible in the submitted image.
-   **Inferred:** plausible interpretation made by the model.
-   **Assumed:** assumption used to draft the ticket.
-   **Unknown:** information that must be collected.

Never convert a reported symptom into a visually verified fact.

### Structured output schema (conceptual)

``` json
{
  "issue_summary": "string",
  "equipment_type": "string|null",
  "equipment_identifier": "string|null",
  "location": "string|null",
  "reported_symptoms": ["string"],
  "visual_observations": ["string"],
  "audio_observations": ["string"],
  "evidence": [
    {
      "source": "user_text|transcript|image",
      "claim": "string",
      "supporting_detail": "string|null"
    }
  ],
  "inferences": ["string"],
  "assumptions": ["string"],
  "unknowns": ["string"],
  "severity": "low|medium|high|unknown",
  "suggested_priority": "low|normal|high|urgent",
  "priority_reason": "string",
  "confidence": "low|medium|high",
  "missing_information": ["string"],
  "safe_checklist": ["string"],
  "technician_message_draft": "string",
  "customer_message_draft": "string",
  "safety_flags": ["string"],
  "requires_human_review": true
}
```

Backend Pydantic schema is authoritative. The JSON above is a design
contract; adapt the exact provider structured-output schema to the
currently supported API.

### Agent tools

Keep tools deterministic and local: - `create_work_order(analysis)` -
`get_work_order(work_order_id)` -
`update_work_order_draft(work_order_id, editable_fields)` -
`approve_work_order(work_order_id)` -
`record_agent_event(run_id, event_type, payload_summary)`

Do not expose arbitrary shell, browser, email, payment, dispatch or
external messaging tools to the product agent.

## 5. Database design

Use SQLite. Suggested tables:

### `work_orders`

-   `id` --- UUID/string primary key
-   `title` --- required string
-   `issue_summary` --- required text
-   `equipment_type` --- nullable string
-   `equipment_identifier` --- nullable string
-   `location` --- nullable string
-   `reported_symptoms_json` --- JSON text
-   `visual_observations_json` --- JSON text
-   `evidence_json` --- JSON text
-   `inferences_json` --- JSON text
-   `assumptions_json` --- JSON text
-   `unknowns_json` --- JSON text
-   `severity` --- enum/string
-   `suggested_priority` --- enum/string
-   `priority_reason` --- text
-   `confidence` --- enum/string
-   `missing_information_json` --- JSON text
-   `safe_checklist_json` --- JSON text
-   `technician_message_draft` --- text
-   `customer_message_draft` --- text
-   `safety_flags_json` --- JSON text
-   `status` --- enum/string, default `draft`
-   `requires_human_review` --- boolean, default true
-   `agent_run_id` --- nullable FK
-   `created_at`, `updated_at`, `approved_at` --- timestamps

### `media_assets`

-   `id` --- UUID/string primary key
-   `work_order_id` --- nullable FK until work order exists
-   `kind` --- `image|audio`
-   `original_filename` --- sanitized name
-   `mime_type`
-   `size_bytes`
-   `storage_path` --- local path; never expose filesystem path to
    browser
-   `created_at`

### `agent_runs`

-   `id` --- UUID/string primary key
-   `status` --- `pending|running|succeeded|failed`
-   `provider` --- `meta|mock`
-   `models_json` --- model IDs used
-   `started_at`, `completed_at`
-   `error_code` --- nullable
-   `error_message_safe` --- nullable user-safe message
-   `duration_ms` --- nullable

### `agent_events`

-   `id` --- integer/UUID primary key
-   `agent_run_id` --- FK
-   `event_type`
-   `stage`
-   `status`
-   `summary` --- concise, non-sensitive description
-   `created_at`

Keep the schema small. JSON columns are acceptable for this
single-workspace MVP. Add migrations only if time and repo conventions
support them.

## 6. API contract

All routes under `/api/v1`.

### `GET /health`

Response:

``` json
{ "status": "ok", "service": "fieldops-api" }
```

### `POST /intakes/analyze`

Content type: `multipart/form-data`

Fields: - `description` --- optional string; require description or
audio. - `image` --- optional image file. - `audio` --- optional audio
file. - `demo_case` --- optional boolean/string only if needed for a
seeded demo.

Behaviour: 1. Validate input. 2. Save attachments temporarily. 3. Create
agent run. 4. Transcribe audio if present. 5. Run Muse Spark analysis.
6. Validate output. 7. Create draft work order. 8. Return the work-order
ID and summary.

Success response (conceptual):

``` json
{
  "work_order": {
    "id": "uuid",
    "status": "draft",
    "title": "Meeting Room 3 — AC not cooling",
    "issue_summary": "..."
  },
  "agent_run": {
    "id": "uuid",
    "status": "succeeded",
    "provider": "meta",
    "stages": [
      {"name": "transcription", "status": "succeeded"},
      {"name": "analysis", "status": "succeeded"},
      {"name": "validation", "status": "succeeded"}
    ]
  }
}
```

Errors must use consistent shape:

``` json
{
  "error": {
    "code": "PROVIDER_UNAVAILABLE",
    "message": "The AI service could not complete the analysis. Please retry.",
    "request_id": "uuid"
  }
}
```

### `GET /work-orders`

Return newest work orders with pagination or a simple limit for MVP.

### `GET /work-orders/{id}`

Return full work order, evidence, media metadata and agent events. Do
not return private filesystem paths.

### `PATCH /work-orders/{id}`

Allow edits only to approved editable fields while status is `draft`.
Validate every field.

### `POST /work-orders/{id}/approve`

-   Only allow `draft` → `approved`.
-   Set `approved_at`.
-   Record audit event.
-   Return updated work order.

### `PATCH /work-orders/{id}/status`

Allow only valid transitions: - `approved` → `in_progress` -
`in_progress` → `completed` - `draft|approved|in_progress` → `cancelled`
Reject invalid transitions with 409.

### `GET /agent-runs/{id}`

Return processing stages and safe error information.

Codex may adjust route naming to match the existing project, but must
keep the contract documented and consistent between frontend and
backend.

## 7. Frontend screens and interaction

### Screen A --- New Intake

Components: - Header: FieldOps AI + Live/Mock indicator. - Text
description textarea. - Image upload with preview. - Audio
upload/recording control (file upload is sufficient for MVP). - Submit
button: "Analyze & Draft Work Order". - Small privacy notice explaining
that uploaded media is sent to the configured AI provider in live mode.

States: - Empty - Validating - Uploading/processing - Validation error -
Provider error with retry - Success → review screen

### Screen B --- Processing

Show real backend stages, not a fake timer: - Validating files -
Transcribing audio (if applicable) - Understanding report - Drafting
work order - Validating result

### Screen C --- Work Order Review

Display: - Status badge: Draft / Approved - Issue summary and editable
title/location/equipment - Priority recommendation + reason - Reported
symptoms - Visual evidence - Transcript - Evidence/source labels -
Inferences, assumptions and unknowns - Missing information - Safe
checklist - Technician and customer message drafts - Approve button

Require explicit confirmation before approval.

### Screen D --- Work Orders list

Simple list/table: - Title - Location - Priority - Status - Created
time - Open details

Do not build a complex analytics dashboard.

## 8. Safety and trust rules

-   UI copy must say "AI-generated draft --- review required".
-   Avoid phrases such as "AI diagnosed the fault" or "confirmed root
    cause".
-   Reported symptoms are not the same as visual observations.
-   A still image cannot establish that a device makes a sound.
-   SAM segmentation locates/segments objects; it does not identify
    damage.
-   Do not instruct a user to open equipment or perform hazardous
    repairs.
-   Flag potentially hazardous symptoms and recommend qualified
    professional review.
-   Never send customer/technician messages automatically.
-   Never auto-dispatch.

## 9. Error handling and resilience

-   Validate file type, size and empty uploads.
-   Use provider timeouts and bounded retries for transient errors only.
-   Normalize provider errors into safe application errors.
-   Do not expose stack traces or API response bodies to the browser.
-   Persist failed agent-run status and stage.
-   Allow retry from the UI.
-   Keep manual text-only intake available if audio/image processing
    fails, but disclose that the result is based on reduced input.
-   Do not silently fall back to mock mode.

## 10. Testing strategy

### Unit tests

-   Pydantic validation rejects invalid enums and malformed arrays.
-   Missing-information and safety rules.
-   Work-order state transitions.
-   Provider adapter request normalization using mocked HTTP.
-   Provider error mapping.
-   File validation.

### Integration tests

-   `POST /intakes/analyze` with mock provider creates a draft.
-   Audio input invokes transcription adapter.
-   Analysis output is validated before persistence.
-   Approve endpoint changes status and records event.
-   Failed provider request creates failed agent run and safe error.

### Manual demo test

1.  Start backend and frontend.
2.  Confirm Live/Mock banner.
3.  Submit sample HVAC case with text + image + audio.
4.  Confirm transcript appears.
5.  Confirm analysis shows evidence/unknowns.
6.  Edit location or title.
7.  Approve work order.
8.  Confirm status and audit event.
9.  Refresh page and confirm persisted record.

## 11. Deployment and security

-   Keep `MODEL_API_KEY` on backend only.
-   Use `.env` locally and ignore it in Git.
-   Provide `.env.example` with placeholders only.
-   Restrict CORS to the frontend origin.
-   Limit uploads and sanitize filenames.
-   Store uploads outside publicly served frontend directories.
-   Do not commit sample images/audio unless you have rights to use
    them.
-   For demo hosting, use a backend host that supports file uploads and
    environment variables; confirm free-tier limits before relying on
    it.
-   If deployment is too risky for the deadline, a stable local demo
    recording is better than an unreliable hosted demo, but the
    repository and run instructions must remain clear.

## 12. Technical source links

Verify current details before coding: - Meta Model API overview:
https://dev.meta.ai/docs/overview - Meta models:
https://dev.meta.ai/docs/models - Meta API reference: navigate from the
official docs above. - Meta quickstart and model-specific guides:
navigate from the official docs above.

The Meta docs currently describe Muse Spark as supporting image
understanding, tool calling and structured output; Muse Voice Transcribe
as speech-to-text; and SAM 3.1 as object segmentation. Confirm exact
request/response schemas, supported formats, rate limits and billing in
the live docs.

## M2 implementation decisions (2026-11-04)

- The Meta adapter uses Python `requests` behind one `MetaClient`. It calls the documented Responses and Voice endpoints with bearer auth, timeout, bounded retries for timeouts and HTTP 429/5xx, and safe error mapping. It logs route, status, latency and request ID only.
- The local root `.env` specifies `META_API_BASE_URL` as the full `/v1/responses` URL. Configuration normalizes that exact documented suffix to `/v1`; other bases must end in `/v1`.
- Spark receives `input_text` and optional base64 JPEG `input_image` blocks. `text.format` requests strict JSON Schema generated by Pydantic. The response is parsed and validated again with `MaintenanceAnalysis`.
- M2 accepts JPEG images and mono 16-bit PCM WAV at 16 or 24 kHz. Audio duration is capped at 10 minutes. The 20 MB app audio limit is below Meta's 32 MB request limit. Other image/audio formats and transcoding are outside M2.
- The pipeline retries invalid model output once, then fails visibly. It rejects evidence citing an absent modality, visual claims about sound/smell/temperature/history, and unsafe checklist or message actions. Hazard words in the supplied text/transcript add escalation and an urgent recommendation for human review.
- Mock mode is selected only by `DEMO_MOCK_MODE=true`; its transcript and drafts are explicitly marked mock. It does not interpret photos. Live mode never falls back to mock. M2 keeps uploads in request memory and does not persist work orders or media.
- Temporary `POST /api/v1/analysis` returns analysis, transcript, mode, provider, models, stages and notice. Errors return a safe code, message, failed stage and mode. M3/M4 will consume this contract.

## M3 implementation decisions (2026-11-04)

- The existing SQLAlchemy engine/session initializes four ORM tables: `work_orders`, `media_assets`, `agent_runs`, and `agent_events`. JSON columns preserve analysis arrays and evidence. SQLite foreign keys are enabled per connection; status and provider check constraints and lookup indexes are present.
- UTC timestamps are stored as ISO text through a SQLAlchemy type decorator and read back as timezone-aware datetimes. UUID strings identify work orders, agent runs and media assets; event IDs are integer keys.
- `POST /api/v1/intakes/analyze` creates a running agent record, validates and stores UUID-named uploads, invokes the existing M2 pipeline once, then commits the draft, media metadata, success events and completed run together. A failure rolls back the draft transaction, deletes newly saved files and commits a failed agent run with a safe error and event. No provider response body, key or local storage path is returned.
- The project-local ignored `.uploads/` directory stores JPEG and WAV files. MIME and extension are checked alongside M2 content/size validation. Original filenames are sanitized metadata only; generated UUID names are used for storage. No media retrieval route exists in M3.
- `GET /api/v1/work-orders` supports newest-first pagination and status filtering. Detail returns the full order, safe media metadata, agent run and event history. `PATCH` edits only approved fields on drafts. `POST /approve` performs explicit draft-to-approved transition with timestamp and audit event. `PATCH /status` applies documented lifecycle transitions; invalid transitions return 409.
- The M3 implementation uses the existing single-workspace, no-auth assumption. The frontend review and approval interaction is deferred to M4.

## M4 implementation decisions (2026-11-04)

- Next.js App Router pages at `/`, `/intake`, `/work-orders`, and `/work-orders/[id]` use client-side calls through one typed API module. `NEXT_PUBLIC_API_BASE_URL` controls only the backend origin; Meta credentials remain server-side.
- The shared application shell reads `/health` for connection and configured live/mock mode. Review pages display the persisted agent-run provider. The synchronous intake UI shows an in-flight state; it renders the actual returned stage records after completion before opening the new work order.
- Intake sends multipart `description`, `image`, and `audio`; browser validation checks JPEG/WAV MIME, filename extension and the default size limits. The backend remains the authority for file contents and configuration-specific limits. Failed requests preserve the form and show the backend's safe error message.
- `GET /api/v1/work-orders/{id}/media/{asset_id}` serves original media. It requires valid UUIDs, verifies the asset belongs to an existing work order, resolves the stored path beneath configured upload storage, restricts suffixes to JPEG/WAV, and sets `private, no-store` and `nosniff` headers. The route is intended only for the current local single-workspace MVP without authentication.
- The review page keeps facts, source-labelled evidence, visual/audio observations, inferences, assumptions, unknowns, missing information, priority rationale and confidence distinct. Draft edits use the existing PATCH contract. Approval uses a native modal confirmation and the existing POST route, then reloads the detail and audit events.
- No browser automation framework was added. A temporary local Chrome DevTools script exercised real browser form submission, media attachment, draft editing, explicit approval, refresh persistence, filters, invalid audio, offline errors and live/mock labels. The temporary script was removed after verification; an audible playback check and a final human visual walkthrough remain useful before the demo recording.

# AGENTS.md --- Instructions for Codex

## Mission

Build **FieldOps AI**, a polished, reliable, demo-ready multimodal
maintenance-intake agent for the Meta Global AI Developer Hackathon.
Treat `docs/PRODUCT_SPEC.md` and `docs/TECHNICAL_DESIGN.md` as the
product source of truth. Treat `docs/IMPLEMENTATION_PLAN.md` as the
execution order.

## Non-negotiable working rules

1.  **Inspect before editing.** Inspect the repository, runtime
    versions, package managers, existing code, and environment variable
    names before changing files.
2.  **Verify Meta APIs before implementation.** Read the current
    official Meta Model API documentation. Never invent endpoint paths,
    request fields, response fields, model IDs, SDK methods, or
    supported audio/image formats. If an API detail is uncertain,
    isolate it behind an adapter and record the uncertainty in
    `docs/BUILD_STATUS.md`.
3.  **No fake AI success.** Never return hard-coded model output while
    presenting it as a live Meta response. Mock mode must be explicitly
    labelled `DEMO_MOCK_MODE=true` and visibly identified in the UI.
4.  **Use Meta models meaningfully.** The core product must make real
    calls to Meta Model API when credentials are configured. Preferred
    MVP integrations:
    -   Muse Voice Transcribe for uploaded audio transcription.
    -   Muse Spark for multimodal issue extraction, structured
        work-order drafting and planning.
    -   SAM 3.1 is optional stretch scope for object segmentation/visual
        evidence. Do not describe SAM as a defect-diagnosis model.
5.  **Build a vertical slice first.** Make one complete case work
    end-to-end before adding secondary features.
6.  **Small, verifiable steps.** Implement one phase at a time. After
    each phase, run relevant tests, type checks, lint and build. Fix
    failures before proceeding.
7.  **Keep project state current.** Create/update `docs/BUILD_STATUS.md`
    with completed work, commands run, test results, blockers, API
    verification notes and next actions.
8.  **Do not over-engineer.** Prefer a modular monolith. Do not add
    microservices, queues, complex agent frameworks, authentication,
    cloud infrastructure or unnecessary abstractions for the MVP.
9.  **Security.** Never commit `.env`, API keys, tokens, customer
    audio/images or private test data. Do not log secrets or full
    sensitive payloads. Validate file types and sizes. Keep uploads
    local and temporary for MVP.
10. **Human approval is mandatory.** Agent-generated work orders remain
    drafts until a human explicitly approves them. Do not automatically
    dispatch technicians, send customer messages, order parts or perform
    physical actions.
11. **Safety boundary.** The app is an administrative triage and
    work-order assistant, not a certified diagnostic or repair
    authority. Do not provide dangerous instructions involving live
    electricity, refrigerants, gas, heights, moving machinery or opening
    equipment. For hazardous/uncertain cases, flag escalation to a
    qualified technician.
12. **Do not claim unsupported facts.** Distinguish observed evidence,
    model inference, assumptions and unknowns. Confidence is not a
    guarantee.
13. **Preserve a working app.** Avoid large rewrites. Do not delete
    existing user work. Do not run destructive commands without explicit
    approval.
14. **Demo-first quality.** The app must have a predictable sample case
    and a clear way to show the actual model path versus mock mode.

## Product decisions

-   Product name: FieldOps AI.
-   Primary persona: small field-service/maintenance team coordinator or
    technician.
-   Initial example domain: HVAC/air-conditioning maintenance.
-   UI language: English-first for the international judging demo; allow
    Vietnamese input where the selected Meta model/API supports it. Do
    not promise language coverage that has not been tested.
-   MVP data: one workspace/local demo, SQLite, no authentication.
-   Core workflow: intake → transcription and image understanding →
    structured issue extraction → safe planning → draft work order →
    human review/approval.
-   Work-order status: `draft`, `approved`, `in_progress`, `completed`,
    `cancelled`.
-   Agent-run status: `pending`, `running`, `succeeded`, `failed`.
-   Keep a clear audit trail of model calls, tool calls, validation and
    user approval.

## API integration guidance

Current official Meta docs surfaced for this project describe: - Base
URL: `https://api.meta.ai/v1` - Auth: Bearer token; official quickstart
uses `MODEL_API_KEY` as the environment variable. - Muse Spark model IDs
include `muse-spark-1.3`, `muse-spark-1.2`, and `muse-spark-1.1`. - Muse
Voice Transcribe model: `muse-voice-transcribe-1.0`; file transcription
route documented as `POST /v1/asr/transcribe`. - SAM 3.1 model ID:
`sam-3.1`; segmentation is exposed through Responses API and Files
API. - Meta docs describe Muse Spark as supporting multimodal
understanding, tool calling and structured output.

These are verification starting points, not permission to guess request
schemas. Confirm current docs and use exact examples/schema. Keep model
IDs configurable. The hackathon guide lists Muse Spark series, Muse
Voice Transcribe and SAM 3.1 as eligible Meta tooling.

## Architecture constraints

-   Backend: Python FastAPI.
-   Frontend: Next.js App Router + TypeScript.
-   Database: SQLite for MVP.
-   ORM: SQLAlchemy 2.x or an existing equivalent already present in
    repo.
-   Validation: Pydantic on backend; Zod or equivalent on frontend if
    useful.
-   Keep Meta provider calls in a dedicated backend service/adapter.
    Never call Meta API directly from browser code.
-   Use environment variables for credentials and model IDs.
-   Use typed schemas and deterministic validation for all
    model-generated JSON.

## Required MVP behaviours

-   User can submit an issue with text, one image, and optionally one
    audio file.
-   If audio is present and live credentials are configured, transcribe
    it using Muse Voice Transcribe.
-   Use Muse Spark to create structured issue details and a work-order
    draft using the text/transcript and image input if supported by the
    verified API path.
-   Persist the work order and processing events.
-   Show evidence and separate `observations`, `inferences`,
    `assumptions`, and `unknowns`.
-   Show suggested priority and reason, but make clear it is a
    recommendation.
-   Generate a safe, non-invasive checklist and draft
    customer/technician messages.
-   Require user review and explicit approval.
-   If provider call fails, show a clear error and allow retry or manual
    text-only intake. Do not silently fall back to fake AI.
-   A clearly labelled mock mode may support UI development and demo
    rehearsals.

## Required quality gates

Before calling a phase complete: - App starts using documented
commands. - Backend health endpoint responds. - Frontend loads without
console-breaking errors. - Core path works in live mode or clearly
labelled mock mode. - Input validation and provider errors are
handled. - Tests cover schema validation, state transitions, provider
adapter behaviour and main API route. - `.env.example` is accurate and
`.env` is ignored. - README contains setup, run, test, live API setup,
mock-mode caveat and demo flow.

## First task

Read all project docs, inspect the repository and verify Meta API
access. Then: 1. Report current repo state and blockers. 2.
Create/update `docs/BUILD_STATUS.md`. 3. Implement only the first
milestone in `docs/IMPLEMENTATION_PLAN.md`. 4. Run checks and report
exact results. 5. Do not continue to the next milestone until the
current one is stable.

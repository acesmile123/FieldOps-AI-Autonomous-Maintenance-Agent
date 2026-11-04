# Implementation Plan --- FieldOps AI

**Deadline basis:** Hackathon guide says Wednesday, November 4, 9:00 PM
Eastern Time. Vietnam is UTC+7; when ET is UTC-5 this converts to
Thursday, November 5, 9:00 AM Vietnam time. Re-check the official
submission platform/timezone before relying on this conversion.

**Execution principle:** Complete a working vertical slice before
optional sophistication.

------------------------------------------------------------------------

## 0. Priority rules

### P0 --- must ship

-   Working frontend and backend.
-   Meta API credentials and at least one successful real Muse Spark
    call.
-   Real Muse Voice Transcribe call when audio is included, if the
    account/API access is available.
-   Structured work-order draft.
-   Evidence / unknowns / assumptions shown separately.
-   Human approval.
-   Error handling.
-   Public repository, README and three-minute demo video.

### P1 --- only after P0 is stable

-   SAM 3.1 segmentation visualization.
-   Better visual polish.
-   Work-order list and status lifecycle.
-   Additional sample cases.

### P2 --- do not build before submission

-   Dispatch, maps, real notifications, inventory, auth, multi-tenant,
    analytics, mobile app, PDF export, multi-agent framework.

## 1. Time-boxed plan

Use the time remaining until the submission deadline. The following
durations are suggested allocations, not fixed clock promises.

  ------------------------------------------------------------------------
  Phase                              Target duration Deliverable
  --------------------- ---------------------------- ---------------------
  Phase 0 ---                             30--45 min Confirm key,
  API/access                                         billing/credits,
  verification                                       successful minimal
                                                     Muse Spark request
                                                     and audio endpoint
                                                     availability

  Phase 1 --- Scaffold                      1--1.5 h Frontend/backend
                                                     start, health
                                                     endpoint, config,
                                                     CORS, SQLite

  Phase 2 --- Core AI                         3--4 h Voice transcription
                                                     adapter + Muse Spark
                                                     structured analysis

  Phase 3 ---                                 2--3 h Schemas, persistence,
  Work-order domain                                  events, state
                                                     transitions

  Phase 4 --- UI                              3--4 h Intake, progress,
  vertical slice                                     review, approve

  Phase 5 ---                                 2--3 h End-to-end live flow,
  Integration hardening                              errors, retry, file
                                                     validation

  Phase 6 --- Demo and                        2--3 h README, tests, GitHub
  submission                                         public, 3-minute
                                                     video, submission

  Buffer                                      1--2 h API issues and final
                                                     fixes
  ------------------------------------------------------------------------

If the deadline is close, remove P1 work. Do not sacrifice a working
core flow to add SAM or decorative UI.

## 2. Phase-by-phase tasks

### Phase 0 --- Verify access before building

-   [ ] Confirm accepted participant status.
-   [ ] Claim the individual \$150 Meta Model API credits (guide says
    each participant claims their own).
-   [ ] Confirm billing/credits and payment-method requirements in Meta
    account.
-   [ ] Create/confirm API key.
-   [ ] Make one minimal Muse Spark request using official quickstart.
-   [ ] Make one minimal Muse Voice Transcribe request using a small
    supported audio sample, if possible.
-   [ ] Confirm exact image input path for Muse Spark.
-   [ ] Record exact model IDs, endpoint, SDK version and request shape
    in `docs/BUILD_STATUS.md`.
-   [ ] Do not start SAM integration yet.

**Exit condition:** at least Muse Spark can be called successfully, or a
blocker is clearly identified with a fallback plan.

### Phase 1 --- Scaffold

-   [ ] Inspect existing repository before changes.
-   [ ] Create backend FastAPI app and `/health`.
-   [ ] Create frontend Next.js app.
-   [ ] Configure CORS.
-   [ ] Configure SQLite and DB session.
-   [ ] Add `.env.example` and `.gitignore`.
-   [ ] Add basic README run commands.
-   [ ] Verify frontend and backend both start.

**Exit condition:** clean local startup.

### Phase 2 --- AI core

-   [ ] Implement Meta client/provider adapter.
-   [ ] Implement Muse Voice Transcribe file upload call.
-   [ ] Implement Muse Spark analysis call.
-   [ ] Create Pydantic response schema.
-   [ ] Create prompt with evidence separation and safety rules.
-   [ ] Add bounded retry for malformed structured output only if
    appropriate.
-   [ ] Add mock provider with visible mock mode.
-   [ ] Add unit tests for adapters and schemas.

**Exit condition:** sample text + image + audio produces a validated
analysis in live mode, or the exact unavailable capability is documented
and the reduced-input path works.

### Phase 3 --- Work-order domain

-   [ ] Create SQLAlchemy models.
-   [ ] Create repositories/services.
-   [ ] Persist work order, media metadata, agent run and events.
-   [ ] Implement valid state transitions.
-   [ ] Implement create/read/update/approve endpoints.
-   [ ] Add tests for persistence and state transitions.

**Exit condition:** work order survives server restart and approval is
auditable.

### Phase 4 --- UI

-   [ ] Build intake form.
-   [ ] Add image/audio upload and previews.
-   [ ] Add processing progress from backend stages.
-   [ ] Build work-order review view.
-   [ ] Show evidence source and uncertainty labels.
-   [ ] Allow draft edits.
-   [ ] Add explicit approval confirmation.
-   [ ] Add work-order list if time permits.
-   [ ] Show live/mock status.

**Exit condition:** user can complete the entire workflow without using
API docs or terminal.

### Phase 5 --- Integration hardening

-   [ ] Test real provider flow.
-   [ ] Test missing key.
-   [ ] Test provider timeout/error.
-   [ ] Test malformed output.
-   [ ] Test unsupported/oversized files.
-   [ ] Test no-audio text + image path.
-   [ ] Test approval and status changes.
-   [ ] Ensure no secret or raw sensitive payload is logged.
-   [ ] Ensure mock mode is visibly labelled.

**Exit condition:** no critical demo-blocking bugs.

### Phase 6 --- Demo and submission

-   [ ] Public GitHub repository.
-   [ ] README with setup, env, run, test, live Meta API and mock-mode
    instructions.
-   [ ] Confirm all project work presented was built during hackathon or
    clearly label pre-existing code.
-   [ ] Confirm repository is accessible without login.
-   [ ] Record a three-minute demo video.
-   [ ] Verify video link is accessible.
-   [ ] List all contributors (solo participant).
-   [ ] Submit through CV platform before deadline.
-   [ ] Save submission confirmation.

## 3. Demo script (180 seconds)

  -----------------------------------------------------------------------
  Time                    What to show            Message
  ----------------------- ----------------------- -----------------------
  0:00--0:20              Problem and intake      Maintenance requests
                          screen                  arrive as scattered
                                                  voice notes, photos and
                                                  text

  0:20--0:55              Upload a photo + voice  FieldOps accepts
                          note                    multimodal evidence

  0:55--1:25              Live processing and     Meta Voice Transcribe
                          transcript              and Muse Spark
                                                  transform unstructured
                                                  input

  1:25--2:05              Generated work order    Evidence, assumptions,
                                                  unknowns, priority
                                                  rationale and checklist
                                                  are explicit

  2:05--2:35              Edit and approve        Human remains in
                                                  control; approval is
                                                  auditable

  2:35--3:00              Impact and technical    Explain time saved from
                          architecture            manual intake and the
                                                  role of Meta models
  -----------------------------------------------------------------------

Avoid long slides. Show the working product. Do not claim measured time
savings unless you actually measured them.

## 4. Final test matrix

  -----------------------------------------------------------------------
  Scenario                            Expected result
  ----------------------------------- -----------------------------------
  Text + image + audio                Transcript + structured draft

  Text + image, no audio              Analysis succeeds without
                                      transcription stage

  Text only                           Reduced-input draft; image
                                      observations absent

  No text and no audio                Validation error

  Invalid file type                   Clear validation error

  Provider unavailable                Safe error, failed run recorded,
                                      retry offered

  Malformed model JSON                Validation/retry or visible
                                      failure; no invalid draft saved

  Hazard words in report              Safety flag and
                                      qualified-professional escalation

  Approve draft                       Status becomes approved and event
                                      recorded

  Approve already approved ticket     Conflict response or idempotent
                                      documented behaviour
  -----------------------------------------------------------------------

## 5. Submission checklist from Hackathon Participant Guide

-   [ ] Public source-code repository.
-   [ ] Demo video exactly/at most the required three-minute duration
    (guide says a three-minute demo video).
-   [ ] Video demonstrates only features/code/functionality built during
    the Hackathon.
-   [ ] New work is clearly identifiable.
-   [ ] All contributors are listed on submission page.
-   [ ] Repository and video links are accessible.
-   [ ] One submission per team; solo participant submits one project.
-   [ ] Submit before the stated deadline; late submissions are not
    considered.

## 6. Build-status template

Create `docs/BUILD_STATUS.md` and maintain this format:

``` md
# Build Status

Updated: YYYY-MM-DD HH:mm TZ

## Current milestone
- Phase:
- Status: not_started | in_progress | blocked | complete

## Completed
- ...

## Commands run
- `...` — PASS/FAIL

## Tests
- ...

## Meta API verification
- Base URL:
- Model IDs:
- Endpoint/schema verified:
- Live call result:
- Billing/credits:
- Known limitations:

## Blockers
- ...

## Next 3 actions
1. ...
2. ...
3. ...
```

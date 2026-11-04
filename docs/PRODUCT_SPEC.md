# Product Specification --- FieldOps AI

**Version:** 1.0\
**Status:** Hackathon MVP specification\
**Track:** Indie Developer\
**Builder:** Solo AI Engineer\
**Primary demo domain:** HVAC / air-conditioning maintenance

------------------------------------------------------------------------

## 1. Product summary

**FieldOps AI** is a multimodal AI maintenance-intake and work-order
assistant. It converts unstructured service requests---voice recordings,
photos and short notes---into a structured, reviewable maintenance work
order.

The product is designed for small maintenance and field-service teams
that currently receive issue reports through calls, chat messages and
photos, then manually rewrite those reports into tickets.

FieldOps AI: 1. Accepts a short text description, one equipment photo
and an optional voice recording. 2. Transcribes audio using Meta Muse
Voice Transcribe. 3. Uses Meta Muse Spark to interpret the report and
produce a structured issue summary. 4. Optionally uses SAM 3.1 to
segment/outline a named object or equipment region in the image, if
integration is verified and time permits. 5. Produces a proposed
priority, missing-information list, safe non-invasive checklist and
work-order draft. 6. Requires a human to review and approve the work
order.

**One-line pitch:** "Turn a voice note and a photo into an
evidence-linked maintenance work order in minutes---with a human in
control."

## 2. Problem

Small maintenance teams often receive incomplete, inconsistent
reports: - A customer calls and describes a symptom verbally. - A
technician receives one or more photos without context. - Someone
manually copies details into a ticketing system. - Important information
such as location, equipment identity, symptoms, urgency and access
constraints may be omitted. - The team has no consistent way to
distinguish what was observed from what was inferred.

This creates administrative overhead, inconsistent triage and avoidable
back-and-forth.

## 3. Target users

### Primary persona --- Service coordinator

-   Works for a small HVAC/facilities maintenance team.
-   Receives issue reports from customers or internal staff.
-   Needs to create consistent work orders quickly.
-   Wants to see the evidence behind AI-generated fields.
-   Must approve the ticket before it becomes operational.

### Secondary persona --- Field technician

-   Sends a voice note and photo from a site.
-   Wants the report transformed into a clear ticket.
-   Needs a checklist of information to verify, not unsafe repair
    instructions.

### MVP user assumptions

-   One local demo workspace.
-   One operator using the application.
-   No authentication or role-based access in the hackathon MVP.
-   No real customer messaging or technician dispatch.

## 4. Product goals

### Must achieve

-   Demonstrate a real Meta-powered multimodal workflow.
-   Reduce manual rewriting of an incoming maintenance report.
-   Produce a structured work order with traceable evidence.
-   Make uncertainty visible.
-   Keep a human approval step before operational use.
-   Work reliably for a controlled three-minute demo.

### Success measures for the demo

These are product/demo targets, not externally validated claims: - A
user can submit a case in under one minute. - A successful run produces
a reviewable work-order draft. - The result includes transcript (when
audio is supplied), issue summary, symptoms, evidence, missing
information, suggested priority, checklist and message drafts. - The
reviewer can edit/approve the draft. - The UI distinguishes live Meta
API mode from mock mode. - A failed provider request is visible and
recoverable.

## 5. Non-goals --- explicitly out of scope

Do not build these for the MVP: - Automatic technician dispatch or route
optimization. - Real email, SMS, WhatsApp or customer notifications. -
Parts purchasing or inventory integration. - Payments, invoicing or CRM
integration. - Multi-tenant SaaS, user authentication or team
permissions. - Mobile native application. - Real-time streaming voice
conversation. - Predictive maintenance or sensor/IoT integration. -
Certified HVAC diagnosis or repair recommendations. - Autonomous
physical actions. - Complex multi-agent architecture. - PDF report
export unless all core acceptance criteria are complete.

## 6. Core user journey

1.  User opens **New Intake**.
2.  User enters a short description, for example: "Meeting room 3 AC is
    not cooling and makes an unusual rattling sound."
3.  User attaches one photo of the equipment.
4.  User optionally attaches a voice recording.
5.  User clicks **Analyze & Draft Work Order**.
6.  UI shows processing stages:
    -   Upload validated
    -   Audio transcription (if audio exists)
    -   Image/report understanding
    -   Issue extraction
    -   Work-order validation
7.  The application displays the draft:
    -   Issue summary
    -   Equipment and location
    -   Reported symptoms
    -   Visual/audio/text evidence
    -   Observations vs. inferences vs. assumptions
    -   Suggested priority and rationale
    -   Missing information
    -   Safe, non-invasive checklist
    -   Draft technician/customer messages
8.  User edits any field that is incorrect.
9.  User clicks **Approve Work Order**.
10. Work order status changes from `draft` to `approved`; the event is
    recorded.

## 7. Functional requirements

### FR-01 --- Intake creation

-   Accept required text description OR at least one audio file.
-   Accept optional image and audio attachments.
-   MVP limit: one image and one audio attachment per intake.
-   Show accepted formats and file-size limits based on actual
    implementation/configuration.
-   Reject unsupported file types and oversized files with actionable
    errors.
-   Never trust the filename or browser MIME type alone;
    inspect/validate content where practical.

### FR-02 --- Audio transcription

-   If audio is attached and live mode is enabled, call Muse Voice
    Transcribe.
-   Save transcript text and provider metadata needed for debugging,
    excluding secrets.
-   Display transcript in the review UI.
-   Allow user to edit the transcript before final approval.
-   If transcription fails, preserve the intake and offer retry or
    text-only continuation.

### FR-03 --- Image understanding

-   Send image to Muse Spark using a currently documented supported
    multimodal input format.
-   Ask the model to describe only visible, relevant evidence and
    identify uncertainty.
-   Do not treat the image model as a certified fault detector.
-   If SAM 3.1 is enabled, use it only to segment/outline a named object
    or region and display the mask/box as visual evidence. Segmentation
    is not proof of a defect.

### FR-04 --- Structured issue extraction

Return a validated object containing: - `issue_summary` -
`equipment_type` - `equipment_identifier` (nullable) - `location`
(nullable) - `reported_symptoms[]` - `visual_observations[]` -
`audio_observations[]` (only if supported by the input/transcript; do
not infer sound from a still image) - `evidence[]` - `inferences[]` -
`assumptions[]` - `unknowns[]` - `severity`:
`low | medium | high | unknown` - `suggested_priority`:
`low | normal | high | urgent` - `priority_reason` - `confidence`:
`low | medium | high` - `missing_information[]` - `safe_checklist[]` -
`technician_message_draft` - `customer_message_draft` -
`requires_human_review`: always `true`

### FR-05 --- Safe planning

-   Checklist items must be administrative or non-invasive observations
    only.
-   The model must not instruct users to open equipment, handle wiring,
    touch electrical components, release/handle refrigerants, work at
    height, bypass safety controls or interact with moving machinery.
-   If the case suggests gas, electrical, refrigerant, fire, smoke,
    burning smell, water near electrical equipment, exposed wiring,
    structural danger or another serious hazard, mark escalation and
    instruct the user to contact a qualified professional/emergency
    service as appropriate.
-   Never state that the AI has confirmed the root cause.

### FR-06 --- Work-order draft

-   Persist a draft work order with a stable ID.
-   User can edit core fields before approval.
-   Store source media references and agent-run ID.
-   Store model-generated content separately from user edits where
    practical.

### FR-07 --- Human approval and status

-   Initial status is `draft`.
-   Explicit approval changes status to `approved`.
-   Record timestamp and approval event.
-   Do not send messages or dispatch anyone after approval in the MVP.
-   Allow status updates to `in_progress`, `completed` and `cancelled`
    for demo lifecycle, with validation.

### FR-08 --- Audit trail

Record meaningful events: - Intake created - File accepted/rejected -
Transcription started/completed/failed - Model analysis
started/completed/failed - Validation failed/retried - Work order
created/edited/approved - Status changed

Do not log API keys or unnecessary raw personal data.

### FR-09 --- Demo mode

-   `DEMO_MOCK_MODE=true` enables deterministic sample outputs for UI
    development and rehearsals.
-   The UI must display a clear **MOCK MODE --- NOT A LIVE MODEL
    RESPONSE** banner.
-   Live mode must call Meta API and show the model/provider path.
-   Never silently switch from live to mock mode.

## 8. Non-functional requirements

-   **Reliability:** provider errors must be surfaced; user can retry.
-   **Latency:** show progress stages; do not promise a fixed processing
    time.
-   **Security:** secrets stay server-side; validate uploads; restrict
    CORS; avoid public exposure of local files.
-   **Privacy:** only collect data needed for the work order; provide
    delete capability for demo records if feasible.
-   **Maintainability:** modular monolith with provider adapters and
    typed schemas.
-   **Observability:** structured logs and persisted agent events with
    correlation IDs.
-   **Accessibility:** clear labels, keyboard-operable controls,
    readable contrast and visible error states.
-   **Demo resilience:** include a sample input and a mock mode, clearly
    labelled.
-   **Portability:** documented local setup; no dependency on a paid
    third-party service other than the configured Meta API.

## 9. Priority and confidence policy

Suggested priority is an assistant recommendation, not an operational
command: - `urgent`: only when the report contains explicit high-risk
indicators or a configured business rule says immediate escalation is
needed. Show the reason and require human confirmation. - `high`:
service impact appears significant, but no immediate hazard is
established. - `normal`: routine maintenance request. - `low`:
informational or non-blocking request. - `unknown`: insufficient
information.

Confidence should reflect completeness/consistency of input, not
probability that a diagnosis is correct. Do not expose fabricated
numerical confidence percentages.

## 10. Demo scenario

### Input

Text: "The air conditioner in Meeting Room 3 is not cooling. There is an
unusual rattling sound. Please inspect it before 3 PM."

Photo: one image showing an indoor HVAC unit.

Audio: a short voice note repeating or adding the issue details.

### Expected output

-   Transcript visible if audio was supplied.
-   Equipment category: air-conditioning unit (if supported by
    evidence).
-   Location: Meeting Room 3 (from user report).
-   Symptoms: not cooling; unusual rattling (reported, not visually
    verified).
-   Visual observations: only what is visibly present in the photo.
-   Unknowns: exact model, asset ID, last maintenance date, whether the
    unit is safe to operate.
-   Suggested priority: `high` or `normal` according to configured
    rules; explain rationale and avoid asserting danger without
    evidence.
-   Checklist: confirm asset ID, confirm access window, ask whether
    there are warning lights/error codes, route to qualified technician
    for inspection.
-   Draft technician message and customer acknowledgement.
-   Human approves the work order.

## 11. Product acceptance criteria

The MVP is acceptable when all are true: 1. Frontend and backend start
from documented commands. 2. User can create an intake with text and at
least one supported attachment or text-only input. 3. Audio path calls
Muse Voice Transcribe in live mode when audio is supplied. 4. Muse Spark
is called for issue extraction/work-order drafting in live mode. 5.
Model output is validated before persistence. 6. Work order shows
evidence, unknowns and assumptions separately. 7. User can edit the
draft and approve it. 8. Approval changes status and creates an audit
event. 9. Provider errors are visible; retry works or user can continue
manually. 10. Mock mode is unmistakably labelled. 11. Tests pass and
README explains live setup. 12. Public GitHub repository contains only
code/assets the participant has rights to use.

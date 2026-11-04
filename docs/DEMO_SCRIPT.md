# FieldOps AI — three-minute demo script

This is a recording plan, not a claim that a submission video already exists. Use a self-owned or rights-cleared HVAC JPEG and a short self-recorded voice report converted to mono 16-bit PCM WAV at 16 or 24 kHz. Keep the media in the ignored local upload area or outside the repository.

## Before recording

1. Start the backend and frontend using [README](../README.md). Check `/health` and the browser header. Use `LIVE META` only when `DEMO_MOCK_MODE=false`, `meta_key_configured=true`, and the account has available credits. A live intake makes paid Meta API calls and requires authorization.
2. Use a separate ignored SQLite file for a clean queue: from `backend/`, set `$env:DATABASE_URL='sqlite:///./demo_fieldops.db'` before starting Uvicorn. Preserve the existing `fieldops.db` and `.uploads/`.
3. Rehearse with `DEMO_MOCK_MODE=true`. The UI must say `MOCK DATA`. Before a live take, restart the backend in live mode and refresh the browser. Have the exact description, photo, and WAV ready. Keep a completed draft from a successful rehearsal available only as an explicitly labelled mock fallback.
4. Set browser zoom so the review page and audit timeline are readable. Keep the recording at or under the duration required by the participant portal; the supplied project plan targets three minutes.

## Recording sequence

| Time | Show and click | Narration |
| --- | --- | --- |
| 0:00–0:20 | Overview, then **New intake**. | “Maintenance reports arrive as a voice note, a photo, and a few words. Coordinators spend time turning them into a usable ticket. FieldOps AI organizes that intake for review.” |
| 0:20–0:48 | Enter: “Meeting Room 3 AC is not cooling and makes a rattling sound.” Attach the rights-cleared JPEG and WAV; briefly show the preview and audio control. | “The report keeps its original evidence. The voice note is transcribed by Meta Muse Voice Transcribe; the photo and text are analyzed by Muse Spark.” |
| 0:48–1:13 | Click **Analyze & create work order**. Show the actual in-flight state, then the returned stages and detail page. | “The request is synchronous. These stage results appear after the backend finishes; they are not simulated streaming progress.” |
| 1:13–1:48 | On the review page, point to the transcript, original media, source-labelled claims, reported symptoms and visual observations. | “Muse Spark produces structured output, and the backend validates it. Reported symptoms and what the photo actually shows stay separate.” |
| 1:48–2:13 | Show inferences, assumptions, unknowns, missing information, priority reason, safety flags and safe checklist. | “The model proposes administrative triage, not a certified equipment diagnosis. Uncertainty and safe escalation remain visible.” |
| 2:13–2:39 | Click **Edit draft**, correct a title or location, save; click **Approve work order**, read the confirmation and confirm. | “A person reviews and edits the draft. Approval is explicit; no technician is dispatched and no customer message is sent.” |
| 2:39–3:00 | Show **Approved**, the approval event in the audit timeline, then **Work orders** filtered to Approved. | “The order and its audit trail persist. FieldOps AI reduces rewriting while keeping the coordinator in control.” |

## If the live API fails

1. Show the safe provider error. Do not describe the failed request as a success.
2. Stop the backend, set `DEMO_MOCK_MODE=true`, restart it, and refresh the browser. Point out `MOCK DATA` before using the deterministic rehearsal path. Say: “This is the labelled mock workflow; the Meta text, image and voice integrations were verified separately during engineering.”
3. Finish the review, edit, approval and audit demonstration. Do not splice mock output into a segment narrated as a live Meta response.

The recording should make the problem, the real Meta role, the human approval boundary and the resulting work order clear without claiming measured time savings or automated repair.

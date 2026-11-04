# FieldOps AI — submission checklist

Status date: 2026-11-05 ICT. Checked boxes are verified locally; unchecked boxes require a participant or external-platform check. [Meta's event page](https://dev.meta.ai/events/global-hackathon) currently lists **November 4, 2026 at 9:00 PM ET** as the submission deadline, equivalent to **November 5 at 9:00 AM ICT**. Meta says dates may change; confirm the time in the participant portal before relying on it.

## Repository and security

- [x] Project has a local Git repository and an initial source-only commit.
- [x] `.gitignore` excludes `.env`, `.env.local`, keys, SQLite, `.uploads/`, virtual environments, build output, caches and TypeScript build info.
- [x] Staged-file scan found no copy of the configured Meta key, private-key block or forbidden release path.
- [x] Push the reviewed source to [GitHub](https://github.com/acesmile123/FieldOps-AI-Autonomous-Maintenance-Agent). Anonymous `git ls-remote` returned the pushed `main` commit and the public raw README returned HTTP 200.
- [ ] Open the public repository in a signed-out browser and verify README, code and docs load. Confirm no media, database, secret or local environment file appears.
- [ ] Confirm all contributors and any pre-existing work are disclosed accurately in the participant submission.

## Application and README

- [x] Backend tests, Python compilation, frontend lint, type check and production build pass. See [BUILD_STATUS](BUILD_STATUS.md) for exact results.
- [x] Mock browser flow covers intake, media, review, edit, explicit approval, audit and filters. Live and mock mode labels were checked separately.
- [x] README contains setup, backend-only key, mode switching, API routes, test commands and local-only deployment boundary.
- [x] The API is documented as a single-workspace local MVP without authentication. Do **not** host the unauthenticated backend on the public internet.
- [ ] On the recording machine, start both services and confirm `/health` plus the dashboard. Confirm a rights-cleared JPEG and a supported WAV are ready.
- [ ] Listen through actual speakers or headphones to the uploaded WAV on the intake preview and review page. Headless Chrome playback advanced, but physical audible output was not measured.
- [ ] If credits and authorization permit, run one full paid live browser intake. Confirm `LIVE META`, provider `meta`, transcript, image evidence and a draft. M2 previously verified live Meta integrations; M5 did not make a paid call.
- [ ] Confirm account-level participant acceptance, credits, billing and API access in Meta's dashboard. A local API key alone does not prove these.

## Demo video

- [ ] Follow [DEMO_SCRIPT](DEMO_SCRIPT.md) for a roughly three-minute problem → solution → human approval story. Verify the participant portal's exact duration and upload rules; the supplied project plan calls for a three-minute video.
- [ ] Show the actual mode badge. If using mock fallback, say it is mock data; do not narrate it as a live model result.
- [ ] Show original evidence, source labels, uncertainty, safe checklist, an edit, explicit approval and the audit event.
- [ ] Check audio intelligibility, cursor visibility, readable text and the final exported duration.
- [ ] Upload the video to the accepted host and open its link signed out. Verify playback and access.

## Final submission

- [ ] Read the accepted participant's official rules and the live portal fields; public event pages do not confirm every submission requirement.
- [ ] Confirm the Indie Developer track and project description match the actual build. Mention Muse Spark and Muse Voice Transcribe; do not claim SAM 3.1 is implemented.
- [ ] Add the public repository and video links, accurate contributor information and any required disclosures.
- [ ] Submit before the portal deadline and save the confirmation. A local commit is not a hackathon submission.

## Local demo-data reset without deleting user data

The current ignored `backend/fieldops.db` contains mock smoke-test work orders. Keep it. For a clean recording, start the backend with `$env:DATABASE_URL='sqlite:///./demo_fieldops.db'` from `backend/`; the app creates a new ignored database. If you later decide to remove existing records or files, first back up both `backend/fieldops.db` and `.uploads/` outside the public repository.

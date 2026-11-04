"use client";
/* eslint-disable @next/next/no-img-element -- local preview object URLs and backend media URLs are not optimized by Next */

import { useEffect, useState, type ChangeEvent, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { PageHeading } from "@/components/app-shell";
import { createIntake, getHealth, type IntakeResult } from "@/lib/api";

function useFileUrl(file: File | null) { const [url, setUrl] = useState(""); useEffect(() => { const next = file ? URL.createObjectURL(file) : ""; let active = true; queueMicrotask(() => { if (active) setUrl(next); }); return () => { active = false; if (next) URL.revokeObjectURL(next); }; }, [file]); return url; }
const size = (file: File) => `${(file.size / (1024 * 1024)).toFixed(1)} MB`;

export default function IntakePage() {
  const router = useRouter();
  const [description, setDescription] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [audio, setAudio] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<IntakeResult | null>(null);
  const [mode, setMode] = useState<"live" | "mock" | null>(null);
  const imageUrl = useFileUrl(image); const audioUrl = useFileUrl(audio);
  useEffect(() => { const c = new AbortController(); getHealth(c.signal).then(h => setMode(h.demo_mock_mode ? "mock" : "live")).catch(() => {}); return () => c.abort(); }, []);
  useEffect(() => { if (!result) return; const timer = setTimeout(() => router.push(`/work-orders/${result.work_order.id}`), 1800); return () => clearTimeout(timer); }, [result, router]);
  function chooseFile(event: ChangeEvent<HTMLInputElement>, kind: "image" | "audio") {
    const file = event.target.files?.[0] ?? null; event.target.value = ""; setError("");
    if (!file) return;
    if (kind === "image") {
      if (!/\.jpe?g$/i.test(file.name) || file.type !== "image/jpeg") return setError("Photo must be a JPEG (.jpg or .jpeg)." );
      if (file.size > 10 * 1024 * 1024) return setError("Photo must be 10 MB or smaller.");
      setImage(file);
    } else {
      if (!/\.wav$/i.test(file.name) || !["audio/wav", "audio/wave", "audio/x-wav"].includes(file.type)) return setError("Recording must be a WAV file.");
      if (file.size > 20 * 1024 * 1024) return setError("Recording must be 20 MB or smaller.");
      setAudio(file);
    }
  }
  async function submit(event: FormEvent) {
    event.preventDefault(); if (busy) return;
    if (!description.trim() && !audio) return setError("Add a description or a voice recording to continue.");
    setError(""); setBusy(true);
    try { setResult(await createIntake(description.trim(), image, audio)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Intake failed. Please retry."); }
    finally { setBusy(false); }
  }
  return <><PageHeading eyebrow="NEW INTAKE / 01" title="Capture the issue." description="Start with what was observed. Add evidence to help the review, then inspect the generated draft before any decision is made." />
    <div className="intake-grid"><form className="panel intake-form" onSubmit={submit}>
      <div className="form-section-title"><span className="step-number">01</span><div><h2>Describe the issue</h2><p>Use the reporter&apos;s words. Avoid making a diagnosis.</p></div></div>
      <label htmlFor="description" className="field-label">Maintenance description <span>Required unless audio is attached</span></label><textarea id="description" className="input textarea" value={description} onChange={e => setDescription(e.target.value)} placeholder="e.g. The air handling unit in the west wing has been making a rattling sound since this morning…" rows={6} disabled={busy} />
      <div className="form-divider" /><div className="form-section-title"><span className="step-number">02</span><div><h2>Add field evidence</h2><p>Optional files stay attached to this work order.</p></div></div>
      <div className="upload-grid"><div className="upload-card"><div className="upload-icon">▧</div><strong>Equipment photo</strong><p>JPEG · Up to 10 MB</p><label className="button secondary upload-button" htmlFor="image-upload">{image ? "Replace photo" : "Choose photo"}</label><input id="image-upload" className="sr-only" type="file" accept=".jpg,.jpeg,image/jpeg" onChange={e => chooseFile(e, "image")} disabled={busy} />{image && <div className="selected-file"><span>{image.name} · {size(image)}</span><button type="button" onClick={() => setImage(null)} disabled={busy}>Remove</button></div>}{imageUrl && <img className="preview-image" src={imageUrl} alt="Selected equipment preview" />}</div>
      <div className="upload-card"><div className="upload-icon">♫</div><strong>Voice recording</strong><p>Mono PCM WAV, 16 or 24 kHz · Up to 20 MB</p><label className="button secondary upload-button" htmlFor="audio-upload">{audio ? "Replace recording" : "Choose recording"}</label><input id="audio-upload" className="sr-only" type="file" accept=".wav,audio/wav,audio/x-wav" onChange={e => chooseFile(e, "audio")} disabled={busy} />{audio && <div className="selected-file"><span>{audio.name} · {size(audio)}</span><button type="button" onClick={() => setAudio(null)} disabled={busy}>Remove</button></div>}{audioUrl && <audio controls src={audioUrl} className="audio-player" aria-label="Selected recording preview" />}</div></div>
      {error && <p role="alert" className="error-box">{error}</p>}
      {busy && <div role="status" className="processing"><span className="spinner" /><div><strong>Processing your intake</strong><p>Validating inputs, analyzing evidence and creating a draft. Confirmed stages will appear when the request finishes.</p></div></div>}
      {result && <div role="status" className="success-box"><strong>Draft work order created</strong><p>{result.mode === "mock" ? "Mock data" : "Live Meta analysis"} · Opening review…</p><div className="stage-list">{result.stages.map((stage, index) => <span key={`${stage.name}-${index}`}>{stage.name}: {stage.status}</span>)}<span>work order: created</span></div><button className="text-link" type="button" onClick={() => router.push(`/work-orders/${result.work_order.id}`)}>Open now →</button></div>}
      <div className="form-footer"><p>AI output remains a draft until you review and approve it.</p><button type="submit" className="button primary" disabled={busy || !!result}>{busy ? "Analyzing…" : "Analyze & create work order →"}</button></div>
    </form><aside className="intake-aside"><div className="side-card"><span className="side-card-icon">✦</span><h3>From report to review</h3><ol><li><b>Capture</b><span>Describe the issue and attach source evidence.</span></li><li><b>Analyze</b><span>{mode === "mock" ? "Mock mode uses clearly labelled sample analysis." : mode === "live" ? "Meta models process submitted evidence." : "Mode is confirmed when the backend connects."}</span></li><li><b>Review</b><span>Edit and explicitly approve the draft.</span></li></ol></div><div className="aside-note">{mode === "mock" ? "MOCK MODE · Generated draft is sample data." : mode === "live" ? "LIVE MODE · Meta processing is enabled." : "BACKEND MODE · Checking connection."}</div></aside></div>
  </>;
}

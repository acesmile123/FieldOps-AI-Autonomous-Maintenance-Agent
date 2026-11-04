export type Health = { status: string; service: string; demo_mock_mode: boolean; meta_key_configured: boolean };
export type Priority = "low" | "normal" | "high" | "urgent";
export type Status = "draft" | "approved" | "in_progress" | "completed" | "cancelled";
export type Evidence = { source: "user_text" | "transcript" | "image"; claim: string; supporting_detail: string | null };
export type WorkOrder = {
  id: string; title: string; issue_summary: string; equipment_type: string | null;
  equipment_identifier: string | null; location: string | null; reported_symptoms: string[];
  visual_observations: string[]; audio_observations: string[]; evidence: Evidence[];
  inferences: string[]; assumptions: string[]; unknowns: string[]; severity: string;
  suggested_priority: Priority; priority_reason: string; confidence: string;
  missing_information: string[]; safe_checklist: string[]; technician_message_draft: string;
  customer_message_draft: string; safety_flags: string[]; transcript: string | null;
  status: Status; requires_human_review: boolean; agent_run_id: string;
  created_at: string; updated_at: string; approved_at: string | null;
};
export type AgentRun = { id: string; status: string; provider: string; models: string[]; started_at: string; completed_at: string | null; duration_ms: number | null; error_code: string | null; error_message_safe: string | null };
export type AgentEvent = { id: number; agent_run_id: string; event_type: string; stage: string; status: string; summary: string; created_at: string };
export type MediaAsset = { id: string; work_order_id: string; kind: string; original_filename: string; mime_type: string; size_bytes: number; created_at: string };
export type WorkOrderDetail = { work_order: WorkOrder; media_assets: MediaAsset[]; agent_run: AgentRun; events: AgentEvent[] };
export type WorkOrderList = { items: WorkOrder[]; total: number; limit: number; offset: number };
export type IntakeResult = { work_order: WorkOrder; agent_run: AgentRun; mode: "live" | "mock"; notice: string | null; stages: { name: string; status: string }[] };
export type WorkOrderUpdate = Pick<WorkOrder, "title" | "issue_summary" | "equipment_type" | "equipment_identifier" | "location" | "suggested_priority" | "priority_reason" | "safe_checklist" | "missing_information" | "technician_message_draft" | "customer_message_draft">;

export const apiBaseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");
export class ApiError extends Error { constructor(message: string, public status: number) { super(message); this.name = "ApiError"; } }
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try { response = await fetch(`${apiBaseUrl}${path}`, { cache: "no-store", ...init }); }
  catch { throw new ApiError("Cannot connect to the backend. Check that it is running, then retry.", 0); }
  if (!response.ok) {
    let message = `Request failed (HTTP ${response.status}).`;
    try {
      const body = await response.json();
      if (typeof body?.error?.message === "string") message = body.error.message;
      else if (typeof body?.detail === "string") message = body.detail;
      else if (Array.isArray(body?.detail)) message = body.detail.map((item: { msg?: string }) => item.msg ?? "Invalid input").join("; ");
    } catch { /* keep the safe HTTP message */ }
    throw new ApiError(message, response.status);
  }
  return response.json() as Promise<T>;
}
export const getHealth = (signal?: AbortSignal) => request<Health>("/health", { signal });
export const listOrders = (status: string, limit: number, offset: number, signal?: AbortSignal) => request<WorkOrderList>(`/api/v1/work-orders?limit=${limit}&offset=${offset}${status ? `&status=${encodeURIComponent(status)}` : ""}`, { signal });
export const getOrder = (id: string, signal?: AbortSignal) => request<WorkOrderDetail>(`/api/v1/work-orders/${encodeURIComponent(id)}`, { signal });
export const mediaUrl = (orderId: string, assetId: string) => `${apiBaseUrl}/api/v1/work-orders/${encodeURIComponent(orderId)}/media/${encodeURIComponent(assetId)}`;
export const createIntake = (description: string, image: File | null, audio: File | null) => {
  const body = new FormData(); body.set("description", description);
  if (image) body.set("image", image); if (audio) body.set("audio", audio);
  return request<IntakeResult>("/api/v1/intakes/analyze", { method: "POST", body });
};
export const updateOrder = (id: string, patch: WorkOrderUpdate) => request<WorkOrderDetail>(`/api/v1/work-orders/${encodeURIComponent(id)}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(patch) });
export const approveOrder = (id: string) => request<WorkOrderDetail>(`/api/v1/work-orders/${encodeURIComponent(id)}/approve`, { method: "POST" });

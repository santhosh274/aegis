/**
 * AEGIS API client — typed fetch + Server-Sent Event streaming + WebSocket.
 * The frontend never talks to Python scripts directly; everything goes through
 * the FastAPI backend (proxied at /api and /ws by Vite).
 */

export const API_BASE = "/api";
export const WS_BASE = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`;

// ── Domain types (mirror core/knowledge_base/models.py) ────────────────
export type ConfidenceGrade = "confirmed" | "suspected" | "needs_human_review";
export type FindingStatus =
  | "open"
  | "confirmed"
  | "remediated"
  | "verified_closed"
  | "reopened"
  | "needs_human_review";
export type Verdict = "verified_closed" | "reopened" | "regression_detected" | "inconclusive";
export type PipelinePhase = "monitor" | "analyze" | "plan" | "execute" | "verify" | "report";
export type PipelineStatus = "running" | "complete" | "failed";

export interface Evidence {
  kind: string;
  summary: string;
  source: string;
  collected_at: string;
  digest: string | null;
  id: string;
}

export interface AttackStep {
  plugin: string;
  action: string;
  target: string;
  expected_predicate: string;
  parameters: Record<string, unknown>;
  id: string;
}

export interface Corroboration {
  probe: string;
  outcome: "supports" | "contradicts" | "ambiguous";
  evidence: Evidence;
  independent: boolean;
  rationale: string;
}

export interface Finding {
  title: string;
  target: string;
  claim: string;
  primary_evidence: Evidence;
  attack_chain: AttackStep[];
  confidence: ConfidenceGrade;
  status: FindingStatus;
  corroborations: Corroboration[];
  id: string;
  created_at: string;
  verification_verdict?: Verdict;
  scenario?: string;
  _path?: string;
}

export interface Observation {
  time: string;
  source: string;
  target: string;
  kind: string;
  value: string;
}

export interface VerificationResult {
  finding_id: string;
  verdict: Verdict;
  evidence: Evidence;
  failed_step_id: string | null;
  regression_summary: string | null;
  completed_at: string;
}

export interface ScopeSettings {
  allowed_hosts: string[];
  allowed_plugins: string[];
  lab_mode: boolean;
  ports: string;
  listener_port: number;
  timeouts: {
    connect: number;
    listen: number;
    replay_wait: number;
  };
}

export interface RunStatus {
  active_scan: boolean;
  active_exploit: boolean;
  active_verify: boolean;
}

export interface PipelineEvent {
  phase: PipelinePhase;
  status: PipelineStatus;
  message: string;
  data?: Record<string, unknown>;
  timestamp: string;
}

export interface EvaluationReport {
  timestamp: string;
  total_findings: number;
  false_positive_rate_adapt_baseline: number;
  false_positive_rate_aegis: number;
  fp_reduction_percent: number;
  confidence_accuracy: number;
  confidence_confusion: Record<string, number>;
  verification_accuracy: number;
  false_all_clear_rate: number;
  verification_confusion: Record<string, number>;
  raw_results: Array<Record<string, unknown>>;
}

export interface VerificationHistoryRow {
  finding_id: string;
  finding_title: string;
  target: string;
  verdict: Verdict;
  timestamp: string;
  target_state: string;
  evidence: string;
}

// ── Typed fetch helpers ────────────────────────────────────────────────
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* keep statusText */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return (await res.json()) as T;
}

export const api = {
  getFindings: () => request<Finding[]>("/findings"),
  getFinding: (id: string) => request<Finding>(`/findings/${encodeURIComponent(id)}`),
  remediate: (id: string) =>
    request<Finding>(`/findings/${encodeURIComponent(id)}/remediate`, { method: "POST" }),
  getStatus: () => request<RunStatus>("/status"),
  getSettings: () => request<ScopeSettings>("/settings"),
  saveSettings: (body: Partial<ScopeSettings>) =>
    request<ScopeSettings>("/settings", { method: "POST", body: JSON.stringify(body) }),
  snapshotBeforeExists: (target: string) =>
    request<{ saved_to: string | null; exists: boolean }>(
      `/snapshot/before?target=${encodeURIComponent(target)}`
    ),
  captureSnapshot: (target: string, label: "before" | "after") =>
    request<{ exposures: Array<{ service: string; port: number }>; saved_to: string }>(
      "/snapshot/capture",
      { method: "POST", body: JSON.stringify({ target, label }) }
    ),
  getVerificationHistory: () => request<VerificationHistoryRow[]>("/verify/history"),
  getEvaluationReport: () => request<EvaluationReport>("/evaluation/report"),
  evaluationSave: (findingPath: string, scenario: string) =>
    request<{ saved_to: string }>("/evaluation/save", {
      method: "POST",
      body: JSON.stringify({ finding_path: findingPath, scenario }),
    }),
};

// ── SSE streaming (POST endpoints → parse text/event-stream body) ─────
export interface SseHandlers {
  onEvent?: (event: PipelineEvent) => void;
  onError?: (error: Error) => void;
}

export async function streamPost(
  path: string,
  body: Record<string, unknown>,
  handlers: SseHandlers,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const payload = await res.json();
      detail = payload.detail ?? detail;
    } catch {
      /* keep statusText */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  if (!res.body) throw new Error("Response body unavailable");
  if (!res.headers.get("content-type")?.includes("text/event-stream")) {
    // Non-stream response (e.g. plain JSON) — surface it as a single event.
    const data = await res.json().catch(() => null);
    handlers.onEvent?.({
      phase: "report",
      status: "complete",
      message: typeof data === "string" ? data : JSON.stringify(data ?? res.status),
      timestamp: new Date().toISOString(),
      data: data as Record<string, unknown>,
    });
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const parseFrame = (frame: string) => {
    const lines = frame.split("\n");
    let eventName = "pipeline";
    const dataLines: string[] = [];
    for (const line of lines) {
      if (line.startsWith("event:")) eventName = line.slice(6).trim();
      else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
    }
    if (dataLines.length === 0) return;
    try {
      const payload = JSON.parse(dataLines.join("\n")) as PipelineEvent;
      handlers.onEvent?.(payload);
    } catch {
      /* ignore malformed frame */
    }
  };

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let sep;
      while ((sep = buffer.indexOf("\n\n")) >= 0) {
        const frame = buffer.slice(0, sep);
        buffer = buffer.slice(sep + 2);
        parseFrame(frame);
      }
    }
    if (buffer.trim().length) parseFrame(buffer);
  } finally {
    reader.releaseLock();
  }
}

// ── WebSocket client for the live finding feed ─────────────────────────
export type WsMessage =
  | { type: "hello"; findings: Finding[] }
  | { type: "finding"; finding: Finding };

export function connectFindingsWs(handlers: {
  onMessage: (msg: WsMessage) => void;
  onClose?: () => void;
}): () => void {
  let closed = false;
  let ws: WebSocket | null = null;
  let retry = 0;

  const open = () => {
    if (closed) return;
    ws = new WebSocket(`${WS_BASE}/findings`);
    ws.onopen = () => {
      retry = 0;
    };
    ws.onmessage = (ev) => {
      try {
        handlers.onMessage(JSON.parse(ev.data as string) as WsMessage);
      } catch {
        /* ignore */
      }
    };
    ws.onclose = () => {
      if (closed) return;
      handlers.onClose?.();
      const delay = Math.min(1000 * 2 ** retry, 8000);
      retry += 1;
      setTimeout(open, delay);
    };
    ws.onerror = () => {
      ws?.close();
    };
  };

  open();
  return () => {
    closed = true;
    ws?.close();
  };
}
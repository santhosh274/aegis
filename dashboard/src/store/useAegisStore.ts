import { create } from "zustand";
import type { Finding, PipelineEvent, RunStatus, ScopeSettings } from "../api/client";

type PhaseState = {
  kind: "idle" | "running" | "complete" | "failed";
  message: string;
};

const IDLE_PHASES: Record<string, PhaseState> = {
  monitor: { kind: "idle", message: "" },
  analyze: { kind: "idle", message: "" },
  plan: { kind: "idle", message: "" },
  execute: { kind: "idle", message: "" },
  verify: { kind: "idle", message: "" },
};

interface AegisState {
  scope: ScopeSettings | null;
  status: RunStatus;
  findings: Finding[];
  phases: Record<string, PhaseState>;
  pipelineEvents: PipelineEvent[];
  setScope: (scope: ScopeSettings) => void;
  setStatus: (status: RunStatus) => void;
  upsertFindings: (findings: Finding[]) => void;
  replaceFindings: (findings: Finding[]) => void;
  pushEvents: (events: PipelineEvent[]) => void;
  clearPipeline: () => void;
  resetPhases: () => void;
}

export const useAegisStore = create<AegisState>((set) => ({
  scope: null,
  status: { active_scan: false, active_exploit: false, active_verify: false },
  findings: [],
  phases: { ...IDLE_PHASES },
  pipelineEvents: [],

  setScope: (scope) => set({ scope }),

  setStatus: (status) => set({ status }),

  upsertFindings: (incoming) =>
    set((state) => {
      let changed = false;
      const map = new Map(state.findings.map((f) => [f.id, f]));
      for (const f of incoming) {
        if (map.has(f.id)) {
          const existing = map.get(f.id)!;
          if (existing.status !== f.status || existing.confidence !== f.confidence) {
            changed = true;
          }
        } else {
          changed = true;
        }
        map.set(f.id, f);
      }
      if (!changed) return state;
      return {
        findings: Array.from(map.values()).sort((a, b) =>
          b.created_at.localeCompare(a.created_at)
        ),
      };
    }),

  replaceFindings: (findings) =>
    set({
      findings: [...findings].sort((a, b) => b.created_at.localeCompare(a.created_at)),
    }),

  pushEvents: (events) =>
    set((state) => {
      const phases = { ...state.phases };
      for (const ev of events) {
        if (ev.phase === "report") continue;
        phases[ev.phase] = {
          kind: ev.status,
          message: ev.message,
        };
      }
      return {
        phases,
        pipelineEvents: [...state.pipelineEvents, ...events].slice(-400),
      };
    }),

  clearPipeline: () => set({ pipelineEvents: [], phases: { ...IDLE_PHASES } }),

  resetPhases: () => set({ phases: { ...IDLE_PHASES } }),
}));

/** Findings awaiting verification: confirmed or reopened, not yet closed. */
export function selectVerificationQueue(findings: Finding[]): Finding[] {
  return findings.filter(
    (f) => f.status === "confirmed" || f.status === "reopened"
  );
}
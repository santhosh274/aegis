import { Check, X, CircleDot } from "lucide-react";
import { cn } from "../lib/utils";
import type { PipelineEvent } from "../api/client";

/**
 * Horizontal MAPE-K-V pipeline. Active phase pulses with a glow (Verify glows red),
 * a thin animated line connects completed phases, and each node shows its current
 * status message. When idle, all nodes are dim.
 */
const NODES = [
  { key: "monitor", label: "Monitor" },
  { key: "analyze", label: "Analyze" },
  { key: "plan", label: "Plan" },
  { key: "execute", label: "Execute" },
  { key: "verify", label: "Verify" },
] as const;

export type PhaseKind = "idle" | "running" | "complete" | "failed";

interface Props {
  /** phase -> state overrides, usually from the live SSE run */
  phases?: Partial<Record<string, { kind: PhaseKind; message: string }>>;
  /** fallback: derive per-phase state from an event log */
  events?: PipelineEvent[];
  compact?: boolean;
}

function stateFor(
  nodeKey: string,
  phases: Props["phases"],
  events: PipelineEvent[] | undefined
): { kind: PhaseKind; message: string } {
  const explicit = phases?.[nodeKey];
  if (explicit) return explicit;
  if (!events) return { kind: "idle", message: "" };
  for (let i = events.length - 1; i >= 0; i--) {
    if (events[i].phase === nodeKey) {
      return { kind: events[i].status, message: events[i].message };
    }
  }
  return { kind: "idle", message: "" };
}

export function PipelineVisualizer({ phases, events, compact }: Props) {
  const states = NODES.map((node) => ({
    node,
    state: stateFor(node.key, phases, events),
  }));

  const connectorClass = (prev: (typeof states)[number]) => {
    if (prev.state.kind === "complete") return "complete";
    if (prev.state.kind === "running")
      return prev.node.key === "verify" ? "verify-flow" : "flowing";
    return "";
  };

  return (
    <div className={cn("flex items-center gap-1", compact ? "py-1" : "py-4")}>
      {states.map(({ node, state }, i) => (
        <div key={node.key} className="flex flex-1 items-center">
          <div
            className={cn(
              "pipeline-node",
              state.kind === "running" && node.key === "verify" && "verify",
              state.kind === "running" && node.key !== "verify" && "active",
              state.kind === "complete" && "complete",
              state.kind === "failed" && "failed"
            )}
          >
            <div className="pipeline-node-circle">
              {state.kind === "complete" ? (
                <Check className="size-4" />
              ) : state.kind === "failed" ? (
                <X className="size-4" />
              ) : state.kind === "running" ? (
                <CircleDot className="size-4 animate-pulse" />
              ) : (
                <span className="font-mono text-[10px]">
                  {String(i + 1).padStart(2, "0")}
                </span>
              )}
            </div>
            <span className="pipeline-node-label">{node.label}</span>
            <span
              className={cn(
                "pipeline-node-detail",
                state.kind === "idle" && "text-muted-foreground"
              )}
            >
              {state.kind === "idle"
                ? "idle"
                : state.kind === "running"
                  ? "running"
                  : state.message || state.kind}
            </span>
          </div>
          {i < states.length - 1 && (
            <div
              className={cn(
                "pipeline-connector",
                connectorClass(states[i])
              )}
            />
          )}
        </div>
      ))}
    </div>
  );
}
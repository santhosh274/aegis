import { useEffect, useRef } from "react";
import { cn } from "../lib/utils";
import type { PipelineEvent } from "../api/client";

const PHASE_LABEL: Record<string, string> = {
  monitor: "MONITOR",
  analyze: "ANALYZE",
  plan: "PLAN",
  execute: "EXECUTE",
  verify: "VERIFY",
  report: "REPORT",
};

/**
 * Live terminal-style log. Each PipelineEvent is a line with a phase-colored
 * prefix tag. Auto-scrolls to the bottom unless the user has scrolled up.
 */
export function TerminalLog({
  events,
  className,
  maxHeight = 320,
}: {
  events: PipelineEvent[];
  className?: string;
  maxHeight?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const stickBottom = useRef(true);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (stickBottom.current) {
      el.scrollTop = el.scrollHeight;
    }
  }, [events.length]);

  const onScroll = () => {
    const el = ref.current;
    if (!el) return;
    stickBottom.current =
      el.scrollHeight - el.scrollTop - el.clientHeight < 24;
  };

  return (
    <div
      ref={ref}
      onScroll={onScroll}
      className={cn("terminal-log overflow-y-auto", className)}
      style={{ maxHeight }}
    >
      {events.length === 0 && (
        <div className="log-line text-muted-foreground">
          <span className="text-border">//</span> waiting for pipeline events…
        </div>
      )}
      {events.map((ev, i) => (
        <div key={i} className="log-line">
          <span className={cn("phase-tag", ev.phase)}>
            [{PHASE_LABEL[ev.phase] ?? ev.phase.toUpperCase()}]
          </span>
          <span className={cn("log-status", ev.status)}>
            {ev.status.toUpperCase()}
          </span>{" "}
          <span className="text-foreground/80">{ev.message}</span>
        </div>
      ))}
      {events.length > 0 && (
        <div className="log-line">
          <span className="text-border">//</span>{" "}
          <span className="text-muted-foreground">
            stream {events[events.length - 1].status === "complete" ? "closed" : "open"}
          </span>
        </div>
      )}
    </div>
  );
}
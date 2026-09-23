import { AlertTriangle } from "lucide-react";
import { cn } from "../lib/utils";
import { ConfidenceBadge } from "./ConfidenceBadge";
import type { Finding } from "../api/client";

/**
 * Live-updating list of findings awaiting verification. Reopened cards carry a
 * red left border; regression-detected cards an orange one with a warning icon.
 */
export function VerificationQueue({
  findings,
  onOpen,
}: {
  findings: Finding[];
  onOpen?: (f: Finding) => void;
}) {
  return (
    <div className="flex flex-col gap-2">
      {findings.length === 0 && (
        <p className="px-1 py-4 text-sm text-muted-foreground">
          Nothing awaiting verification right now.
        </p>
      )}
      {findings.map((f) => (
        <button
          key={f.id}
          onClick={() => onOpen?.(f)}
          className={cn(
            "queue-card text-left rounded-md border border-border bg-surface p-3 transition-colors hover:border-muted-foreground/50",
            f.status === "reopened" && "reopened",
            f.verification_verdict === "regression_detected" && "regression_detected"
          )}
        >
          <div className="flex items-start justify-between gap-2">
            <span className="text-xs font-medium leading-snug text-foreground/90">
              {f.title}
            </span>
            {f.verification_verdict === "regression_detected" && (
              <AlertTriangle className="size-3.5 shrink-0 text-regression" />
            )}
          </div>
          <div className="mt-2 flex items-center justify-between gap-2">
            <span className="font-mono text-[11px] text-muted-foreground">
              {f.target}
            </span>
            <ConfidenceBadge grade={f.confidence} />
          </div>
        </button>
      ))}
    </div>
  );
}
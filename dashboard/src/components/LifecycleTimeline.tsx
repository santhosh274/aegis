import { Check, Lock, RotateCcw, Wrench } from "lucide-react";
import { cn, formatTime } from "../lib/utils";
import type { Finding } from "../api/client";

interface Milestone {
  key: string;
  label: string;
  reached: boolean;
  at?: string;
  icon?: React.ReactNode;
  tone?: "green" | "red" | "cyan";
}

function verifyingMilestone(f: Finding): { reached: boolean; at?: string; tone: "green" | "red" } {
  const verdict = f.verification_verdict;
  if (verdict === "verified_closed")
    return { reached: true, at: f.created_at, tone: "green" };
  if (verdict === "reopened" || verdict === "regression_detected")
    return { reached: true, at: f.created_at, tone: "red" };
  if (f.status === "verified_closed") return { reached: true, at: f.created_at, tone: "green" };
  if (f.status === "reopened") return { reached: true, at: f.created_at, tone: "red" };
  return { reached: false, tone: "green" };
}

/**
 * Horizontal lifecycle timeline: Opened → Confirmed → Remediated (if applicable)
 * → Verified / Reopened (if applicable). Each reached node shows a timestamp.
 */
export function LifecycleTimeline({ finding }: { finding: Finding }) {
  const remediated = finding.status === "remediated" || finding.status === "verified_closed" || finding.status === "reopened" || finding.status === "needs_human_review";
  const verified = verifyingMilestone(finding);

  const milestones: Milestone[] = [
    { key: "opened", label: "Opened", reached: true, at: finding.created_at },
    {
      key: "confirmed",
      label: "Confirmed",
      reached: finding.status === "confirmed" || remediated || verified.reached,
      at: finding.created_at,
      icon: <Check className="size-3.5" />,
      tone: "green",
    },
    ...(remediated || verified.reached
      ? [
          {
            key: "remediated",
            label: "Remediated",
            reached: remediated,
            at: finding.created_at,
            icon: <Wrench className="size-3.5" />,
            tone: "cyan" as const,
          },
        ]
      : []),
    {
      key: "verified",
      label:
        finding.verification_verdict === "reopened" ||
        finding.status === "reopened"
          ? "Reopened"
          : "Verified",
      reached: verified.reached,
      at: verified.at,
      icon: verified.tone === "red" ? <RotateCcw className="size-3.5" /> : <Lock className="size-3.5" />,
      tone: verified.tone,
    },
  ];

  return (
    <div className="flex items-center w-full">
      {milestones.map((m, i) => (
        <div key={m.key} className="flex flex-1 items-center last:flex-none">
          <div className="flex flex-col items-center gap-1">
            <div
              className={cn(
                "flex h-8 w-8 items-center justify-center rounded-full border-2",
                m.reached
                  ? m.tone === "red"
                    ? "border-destructive text-destructive bg-destructive/10"
                    : m.tone === "cyan"
                      ? "border-cyan text-cyan bg-cyan/10"
                      : "border-success text-success bg-success/10"
                  : "border-border text-muted-foreground bg-surface"
              )}
            >
              {m.icon ?? <span className="h-1.5 w-1.5 rounded-full bg-current" />}
            </div>
            <span className={cn("font-mono text-[10px] font-semibold", m.reached ? "text-foreground" : "text-muted-foreground")}>
              {m.label}
            </span>
            <span className="font-mono text-[9px] text-muted-foreground">
              {m.reached && m.at ? formatTime(m.at) : "—"}
            </span>
          </div>
          {i < milestones.length - 1 && (
            <div
              className={cn(
                "h-px flex-1 mx-1 mb-6",
                milestones[i].reached && milestones[i + 1]?.reached
                  ? milestones[i + 1]?.tone === "red"
                    ? "bg-destructive"
                    : "bg-success"
                  : "bg-border"
              )}
            />
          )}
        </div>
      ))}
    </div>
  );
}
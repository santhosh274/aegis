import { Lock, RotateCcw, ShieldAlert } from "lucide-react";
import { cn } from "../lib/utils";
import type { FindingStatus } from "../api/client";

const LABEL: Record<FindingStatus, string> = {
  open: "Opened",
  confirmed: "Confirmed",
  remediated: "Remediated",
  verified_closed: "Verified Closed",
  reopened: "Reopened",
  needs_human_review: "Needs Review",
};

const ICON: Partial<Record<FindingStatus, React.ReactNode>> = {
  verified_closed: <Lock className="size-3" />,
  reopened: <RotateCcw className="size-3" />,
  confirmed: <ShieldAlert className="size-3" />,
};

/** Pill-shaped lifecycle status chip. */
export function LifecycleChip({
  status,
  className,
}: {
  status: FindingStatus;
  className?: string;
}) {
  return (
    <span className={cn("lifecycle-chip", status, className)}>
      {ICON[status]}
      {LABEL[status] ?? status}
    </span>
  );
}

export function lifecycleLabel(status: FindingStatus): string {
  return LABEL[status] ?? status;
}
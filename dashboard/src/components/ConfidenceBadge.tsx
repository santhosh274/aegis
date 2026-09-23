import { cn } from "../lib/utils";
import type { ConfidenceGrade } from "../api/client";

const LABEL: Record<ConfidenceGrade, string> = {
  confirmed: "Confirmed",
  suspected: "Suspected",
  needs_human_review: "Needs Human Review",
};

/**
 * Color-coded grade badge. Confirmed=green, Suspected=amber,
 * Needs Human Review=grey with a dashed border. The badge is driven purely by
 * finding.confidence — never by whether the primary exploit succeeded.
 */
export function ConfidenceBadge({
  grade,
  size = "sm",
  className,
}: {
  grade: ConfidenceGrade;
  size?: "sm" | "lg";
  className?: string;
}) {
  return (
    <span
      className={cn("confidence-badge", grade, size === "lg" && "text-xs px-3 py-1", className)}
    >
      {LABEL[grade] ?? grade}
    </span>
  );
}
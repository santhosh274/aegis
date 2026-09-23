import type { Finding } from "../api/client";

export type Severity = "high" | "medium" | "low";

/**
 * Cosmetic severity chip derived from the vulnerability arms the finding
 * describes. The AEGIS Finding model carries no severity field, so the feed
 * chip maps known exploit arms to a severity band.
 */
export function severityFor(finding: Finding): Severity {
  const hay = `${finding.title} ${finding.primary_evidence.kind} ${finding.claim}`.toLowerCase();
  if (hay.includes("backdoor") || hay.includes("root") || hay.includes("shell")) {
    return "high";
  }
  if (hay.includes("rce") || hay.includes("remote code")) {
    return "high";
  }
  if (hay.includes("exposure") || hay.includes("credential")) {
    return "medium";
  }
  return "low";
}

const STYLE: Record<Severity, string> = {
  high: "text-destructive border-destructive/50 bg-destructive/10",
  medium: "text-warning border-warning/50 bg-warning/10",
  low: "text-cyan border-cyan/50 bg-cyan/10",
};

export function severityChip(finding: Finding): { label: string; className: string } {
  const s = severityFor(finding);
  return { label: s.toUpperCase(), className: STYLE[s] };
}
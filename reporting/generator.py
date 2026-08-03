"""Evidence-backed Markdown report renderer; PDF rendering can wrap this output."""
from __future__ import annotations

from core.knowledge_base.models import Finding, VerificationResult


def render_finding(finding: Finding, verification: VerificationResult | None = None) -> str:
    lines = [
        f"## {finding.title}",
        "",
        f"- Target: `{finding.target}`",
        f"- Claim: {finding.claim}",
        f"- Confidence: **{finding.confidence.value}**",
        f"- Lifecycle status: **{finding.status.value}**",
        f"- Primary evidence: {finding.primary_evidence.summary} ({finding.primary_evidence.source})",
        "",
        "### Corroboration",
    ]
    lines.extend(f"- {item.probe}: **{item.outcome.value}** — {item.evidence.summary}" for item in finding.corroborations)
    if verification:
        lines.extend(["", "### Post-remediation verification", f"- Verdict: **{verification.verdict.value}**", f"- Evidence: {verification.evidence.summary}"])
        if verification.regression_summary:
            lines.append(f"- Regression: {verification.regression_summary}")
    return "\n".join(lines) + "\n"

# AEGIS architecture

AEGIS implements MAPE-K-V: **Monitor** normalizes observations; **Analyze** maintains
the model and grades evidence; **Plan** ranks permitted next actions by utility;
**Execute** is scope-gated; a devil's-advocate pass obtains independent
corroboration; **Verify** replays a recorded declarative chain after remediation and
returns `verified_closed`, `reopened`, `regression_detected`, or `inconclusive`.

The knowledge ledger holds immutable evidence references, findings, remediation
events, and verification results. Confidence is intentionally separate from utility:
utility decides what to attempt, while confidence decides how strongly to report a
claim.

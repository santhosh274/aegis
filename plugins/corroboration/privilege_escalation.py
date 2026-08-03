"""Privilege corroboration adapter using an externally supplied safe role check."""
from core.knowledge_base.models import Corroboration, CorroborationOutcome, Evidence, Finding


class PrivilegeEscalationCorroborator:
    name = "privilege_escalation"
    def __init__(self, role_matches: bool | None): self.role_matches = role_matches
    def corroborate(self, finding: Finding) -> Corroboration:
        outcome = CorroborationOutcome.AMBIGUOUS if self.role_matches is None else (CorroborationOutcome.SUPPORTS if self.role_matches else CorroborationOutcome.CONTRADICTS)
        return Corroboration(self.name, outcome, Evidence("role_check", "independent effective-role check", self.name), True, "fresh session")

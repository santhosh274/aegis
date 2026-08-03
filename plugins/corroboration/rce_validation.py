"""RCE corroboration is modelled as a benign nonce predicate, not command payloads."""
from core.knowledge_base.models import Corroboration, CorroborationOutcome, Evidence, Finding


class RceCorroborator:
    name = "rce_validation"

    def __init__(self, nonce_observed: bool | None):
        self.nonce_observed = nonce_observed

    def corroborate(self, finding: Finding) -> Corroboration:
        outcome = CorroborationOutcome.AMBIGUOUS if self.nonce_observed is None else (CorroborationOutcome.SUPPORTS if self.nonce_observed else CorroborationOutcome.CONTRADICTS)
        summary = "benign nonce result was indeterminate" if self.nonce_observed is None else ("benign nonce observed in independent session" if self.nonce_observed else "benign nonce was not observed")
        return Corroboration(self.name, outcome, Evidence("rce_check", summary, self.name), True, "separate session and nonce predicate")

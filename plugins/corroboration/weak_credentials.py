"""Safe corroboration contract; integrations provide a fresh-session result."""
from core.knowledge_base.models import Corroboration, CorroborationOutcome, Evidence, Finding


class WeakCredentialCorroborator:
    name = "weak_credentials"

    def __init__(self, fresh_login_succeeds: bool | None):
        self.fresh_login_succeeds = fresh_login_succeeds

    def corroborate(self, finding: Finding) -> Corroboration:
        if self.fresh_login_succeeds is None:
            outcome = CorroborationOutcome.AMBIGUOUS
            summary = "fresh-session authentication could not be established"
        elif self.fresh_login_succeeds:
            outcome, summary = CorroborationOutcome.SUPPORTS, "fresh independent session authenticated"
        else:
            outcome, summary = CorroborationOutcome.CONTRADICTS, "fresh independent session rejected credentials"
        return Corroboration(self.name, outcome, Evidence("credential_check", summary, self.name), True, "separate session")

"""Data-exposure corroboration adapter using a minimal approved sample predicate."""
from core.knowledge_base.models import Corroboration, CorroborationOutcome, Evidence, Finding


class DataExposureCorroborator:
    name = "data_exposure"
    def __init__(self, schema_matches: bool | None): self.schema_matches = schema_matches
    def corroborate(self, finding: Finding) -> Corroboration:
        outcome = CorroborationOutcome.AMBIGUOUS if self.schema_matches is None else (CorroborationOutcome.SUPPORTS if self.schema_matches else CorroborationOutcome.CONTRADICTS)
        return Corroboration(self.name, outcome, Evidence("data_check", "minimal approved schema validation", self.name), True, "separate retrieval and schema check")

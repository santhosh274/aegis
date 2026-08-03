import pytest
from config.settings import ScopePolicy
from core.execute.executor import Executor
from core.knowledge_base.models import AttackStep, Evidence


class FixturePlugin:
    name = "fixture"
    def run(self, step): return Evidence("fixture", "ran", self.name)


def test_executor_enforces_lab_scope():
    executor = Executor(ScopePolicy(("10.0.0.0/24",), (), ("fixture",)), {"fixture": FixturePlugin()})
    assert executor.execute(AttackStep("fixture", "check", "10.0.0.5", "ok")).summary == "ran"
    with pytest.raises(PermissionError):
        executor.execute(AttackStep("fixture", "check", "8.8.8.8", "ok"))

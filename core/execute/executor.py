"""Scope-gated managed-system executor.

Live adapters are intentionally not supplied by this repository.  The executor
only calls registered, reviewed adapters after checking lab scope.
"""
from __future__ import annotations

from typing import Protocol
from config.settings import ScopePolicy
from core.knowledge_base.models import AttackStep, Evidence


class ActionPlugin(Protocol):
    name: str
    def run(self, step: AttackStep) -> Evidence: ...


class Executor:
    def __init__(self, policy: ScopePolicy, plugins: dict[str, ActionPlugin]):
        self.policy = policy
        self.plugins = plugins

    def execute(self, step: AttackStep) -> Evidence:
        if not self.policy.lab_mode:
            raise PermissionError("AEGIS execution is lab-only by default")
        if not self.policy.permits_target(step.target):
            raise PermissionError(f"target is outside authorized scope: {step.target}")
        if not self.policy.permits_plugin(step.plugin):
            raise PermissionError(f"plugin is not authorized: {step.plugin}")
        if step.plugin not in self.plugins:
            raise KeyError(f"no registered plugin: {step.plugin}")
        return self.plugins[step.plugin].run(step)

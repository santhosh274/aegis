"""Persistence seam for a future SQLAlchemy/PostgreSQL implementation."""
from typing import Protocol
from .models import Finding


class FindingRepository(Protocol):
    def save(self, finding: Finding) -> None: ...
    def get(self, finding_id: str) -> Finding | None: ...

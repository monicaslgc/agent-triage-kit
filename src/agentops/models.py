"""Core data types shared by every agent and the orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Category(str, Enum):
    INFRASTRUCTURE = "infrastructure"
    INTEGRATION = "integration"
    AUTH = "auth"
    DATA = "data"
    UNKNOWN = "unknown"


@dataclass
class Ticket:
    """A support/engineering ticket coming into the system."""

    id: str
    title: str
    body: str
    reporter: str = "unknown"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Action:
    """One step an agent took, kept for the audit trail in the final Report."""

    agent: str
    summary: str
    detail: str = ""
    confidence: float = 0.0  # 0..1, how sure the agent is about `summary`


@dataclass
class Report:
    """Final output of the pipeline for a single ticket."""

    ticket: Ticket
    severity: Severity
    category: Category
    actions: list[Action] = field(default_factory=list)
    resolved: bool = False
    escalated_to_human: bool = False
    recommendation: Optional[str] = None

    def add(self, action: Action) -> None:
        self.actions.append(action)

    def __str__(self) -> str:  # pragma: no cover - convenience/formatting only
        lines = [
            f"Ticket {self.ticket.id}: {self.ticket.title}",
            f"  severity={self.severity.value} category={self.category.value}",
        ]
        for a in self.actions:
            lines.append(f"  [{a.agent}] {a.summary} (confidence={a.confidence:.2f})")
        outcome = (
            "escalated to human"
            if self.escalated_to_human
            else "resolved" if self.resolved else "no action taken"
        )
        lines.append(f"  -> {outcome}")
        if self.recommendation:
            lines.append(f"  recommendation: {self.recommendation}")
        return "\n".join(lines)

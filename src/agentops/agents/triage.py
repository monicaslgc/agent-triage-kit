"""TriageAgent: the first stop for every incoming ticket.

Its only job is to read the raw title/body and decide (a) how urgent this
is and (b) what kind of problem it looks like. Everything downstream
(investigation depth, escalation threshold) depends on this classification,
so it's kept intentionally simple and explainable rather than clever.
"""

from __future__ import annotations

from ..agent import Agent
from ..models import Action, Category, Report, Severity, Ticket

_CRITICAL_WORDS = ("outage", "down", "critical", "data loss", "breach")
_HIGH_WORDS = ("failing", "error", "broken", "blocked", "urgent")

_CATEGORY_WORDS: dict[Category, tuple[str, ...]] = {
    Category.AUTH: ("token", "login", "unauthorized", "401", "403", "auth"),
    Category.INTEGRATION: ("webhook", "integration", "callback", "api", "500"),
    Category.INFRASTRUCTURE: ("server", "database", "db", "timeout", "cpu", "memory", "disk"),
    Category.DATA: ("duplicate", "missing data", "incorrect data", "sync"),
}


class TriageAgent(Agent):
    name = "triage"

    def run(self, ticket: Ticket, report: Report) -> Action:
        text = f"{ticket.title} {ticket.body}".lower()

        severity = Severity.LOW
        if any(w in text for w in _CRITICAL_WORDS):
            severity = Severity.CRITICAL
        elif any(w in text for w in _HIGH_WORDS):
            severity = Severity.HIGH
        elif len(text) > 0:
            severity = Severity.MEDIUM

        category = Category.UNKNOWN
        best_hits = 0
        for cat, words in _CATEGORY_WORDS.items():
            hits = sum(1 for w in words if w in text)
            if hits > best_hits:
                category, best_hits = cat, hits

        report.severity = severity
        report.category = category

        confidence = 0.9 if best_hits > 0 else 0.4
        return Action(
            agent=self.name,
            summary=f"classified as {severity.value}/{category.value}",
            detail=f"matched {best_hits} category keyword(s)",
            confidence=confidence,
        )

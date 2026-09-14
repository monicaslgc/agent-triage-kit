"""InvestigatorAgent: tries to find a likely root cause before a human gets paged.

It checks the ticket text against a small runbook of known issue patterns.
A real deployment would swap `runbook.match()` for a lookup over historical
incidents or a call to `self.brain` -- the rest of the pipeline doesn't care
which one produced the diagnosis, only the resulting confidence.
"""

from __future__ import annotations

from ..agent import Agent
from ..models import Action, Report, Ticket
from .. import runbook


class InvestigatorAgent(Agent):
    name = "investigator"

    def run(self, ticket: Ticket, report: Report) -> Action:
        text = f"{ticket.title} {ticket.body}"
        issue = runbook.match(text)

        if issue is None:
            return Action(
                agent=self.name,
                summary="no matching known issue found",
                detail="ticket does not match any runbook pattern",
                confidence=0.2,
            )

        report.recommendation = issue.next_step
        return Action(
            agent=self.name,
            summary=issue.diagnosis,
            detail=f"next step: {issue.next_step}",
            confidence=issue.confidence,
        )

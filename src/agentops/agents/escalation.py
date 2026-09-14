"""EscalationAgent: decides whether a ticket gets auto-resolved or handed to a human.

This is really the piece that determines whether the pipeline is worth
trusting. Escalate too eagerly and the automation does nothing useful.
Escalate too rarely and low-confidence guesses reach users unchecked. The
thresholds below are the one knob I'd actually expect someone to tune.
"""

from __future__ import annotations

from ..agent import Agent
from ..models import Action, Report, Severity, Ticket

# Tunable policy: below this confidence in the investigation, or at/above
# this severity, a human reviews before anything is considered resolved.
MIN_AUTO_RESOLVE_CONFIDENCE = 0.7
ALWAYS_ESCALATE_SEVERITIES = (Severity.CRITICAL,)


class EscalationAgent(Agent):
    name = "escalation"

    def run(self, ticket: Ticket, report: Report) -> Action:
        investigation_confidence = max(
            (a.confidence for a in report.actions if a.agent == "investigator"),
            default=0.0,
        )

        must_escalate = report.severity in ALWAYS_ESCALATE_SEVERITIES
        low_confidence = investigation_confidence < MIN_AUTO_RESOLVE_CONFIDENCE

        if must_escalate or low_confidence:
            report.escalated_to_human = True
            report.resolved = False
            reason = (
                f"severity={report.severity.value} requires human review"
                if must_escalate
                else f"investigation confidence {investigation_confidence:.2f} below threshold"
            )
            return Action(
                agent=self.name,
                summary="escalated to human",
                detail=reason,
                confidence=1.0,
            )

        report.escalated_to_human = False
        report.resolved = True
        return Action(
            agent=self.name,
            summary="auto-resolved",
            detail=f"investigation confidence {investigation_confidence:.2f} met threshold",
            confidence=investigation_confidence,
        )

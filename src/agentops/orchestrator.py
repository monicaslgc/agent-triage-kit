"""Orchestrator: runs the agent pipeline over a ticket and produces a Report."""

from __future__ import annotations

from .agent import Agent
from .agents import EscalationAgent, InvestigatorAgent, TriageAgent
from .brain import LLMClient
from .models import Category, Report, Severity, Ticket


class Orchestrator:
    """Runs a fixed pipeline of agents in order, building up a Report.

    Kept this linear on purpose (triage -> investigate -> escalate) instead
    of building out a general graph executor. Each stage just needs the
    previous stage's output and there's no branching, so a DAG would be
    over-engineering for what this actually does. If the problem grows more
    complex later, that's the point where I'd reach for something fancier.
    """

    def __init__(
        self,
        brain: LLMClient | None = None,
        agents: list[Agent] | None = None,
    ) -> None:
        self.agents = agents or [
            TriageAgent(brain=brain),
            InvestigatorAgent(brain=brain),
            EscalationAgent(brain=brain),
        ]

    def process(self, ticket: Ticket) -> Report:
        report = Report(ticket=ticket, severity=Severity.LOW, category=Category.UNKNOWN)
        for agent in self.agents:
            action = agent.run(ticket, report)
            report.add(action)
        return report

    def process_batch(self, tickets: list[Ticket]) -> list[Report]:
        return [self.process(t) for t in tickets]

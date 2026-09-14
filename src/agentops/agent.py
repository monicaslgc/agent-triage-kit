"""Base class every specialized agent inherits from."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .brain import LLMClient
from .models import Action, Report, Ticket


class Agent(ABC):
    """A single-responsibility step in the pipeline.

    Each agent reads the ticket (and the report built so far by earlier
    agents), does one job, and appends an Action describing what it did.
    Keeping agents single-responsibility is what makes the pipeline easy to
    test and to reorder/extend.
    """

    name: str = "agent"

    def __init__(self, brain: LLMClient | None = None) -> None:
        self.brain = brain

    @abstractmethod
    def run(self, ticket: Ticket, report: Report) -> Action:
        """Perform this agent's job and return the Action it took.

        Implementations may also mutate `report` (e.g. set severity/category)
        in addition to returning an Action for the audit trail.
        """
        raise NotImplementedError

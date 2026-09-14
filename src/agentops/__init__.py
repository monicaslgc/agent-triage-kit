"""agentops: a small, readable framework for multi-agent ticket triage & escalation.

This package is a self-contained demo. It has no external dependencies and
no network calls by default -- every "agent" is a plain Python class that
makes a decision from rules or a small in-memory knowledge base. The
`LLMClient` protocol in `brain.py` shows where a real model call would slot
in without changing any orchestration logic.
"""

from .models import Ticket, Action, Report
from .orchestrator import Orchestrator

__all__ = ["Ticket", "Action", "Report", "Orchestrator"]
__version__ = "0.1.0"

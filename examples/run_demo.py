#!/usr/bin/env python3
"""Run the agent pipeline over the sample tickets and print a report.

Usage:
    python examples/run_demo.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agentops import Orchestrator, Ticket  # noqa: E402


def load_tickets(path: Path) -> list[Ticket]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Ticket(id=d["id"], title=d["title"], body=d["body"], reporter=d.get("reporter", "unknown")) for d in data]


def main() -> None:
    tickets_path = Path(__file__).resolve().parent / "tickets.json"
    tickets = load_tickets(tickets_path)

    orchestrator = Orchestrator()
    reports = orchestrator.process_batch(tickets)

    auto_resolved = sum(1 for r in reports if r.resolved)
    escalated = sum(1 for r in reports if r.escalated_to_human)

    for report in reports:
        print(report)
        print("-" * 60)

    print(f"\n{len(reports)} tickets processed: {auto_resolved} auto-resolved, {escalated} escalated to a human.")


if __name__ == "__main__":
    main()

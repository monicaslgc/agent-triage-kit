import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agentops import Orchestrator, Ticket
from agentops.models import Category, Severity


def make_ticket(**overrides) -> Ticket:
    defaults = dict(id="T-TEST", title="", body="", reporter="test")
    defaults.update(overrides)
    return Ticket(**defaults)


def test_critical_ticket_is_always_escalated():
    orchestrator = Orchestrator()
    ticket = make_ticket(title="Full outage", body="Critical: everything is down, data loss risk.")

    report = orchestrator.process(ticket)

    assert report.severity == Severity.CRITICAL
    assert report.escalated_to_human is True
    assert report.resolved is False


def test_known_auth_issue_auto_resolves():
    orchestrator = Orchestrator()
    ticket = make_ticket(
        title="Login broken",
        body="User gets 401 unauthorized, token expired error when logging in.",
    )

    report = orchestrator.process(ticket)

    assert report.category == Category.AUTH
    # Known pattern with confidence 0.8 clears the 0.7 auto-resolve threshold.
    assert report.resolved is True
    assert report.escalated_to_human is False
    assert report.recommendation is not None


def test_unrecognized_ticket_escalates_on_low_confidence():
    orchestrator = Orchestrator()
    ticket = make_ticket(title="Weird thing", body="Something looks off, not sure what.")

    report = orchestrator.process(ticket)

    assert report.escalated_to_human is True
    assert report.resolved is False


def test_every_agent_leaves_an_audit_trail_entry():
    orchestrator = Orchestrator()
    ticket = make_ticket(title="Webhook 500", body="Integration callback returning 500 errors.")

    report = orchestrator.process(ticket)

    agent_names = [a.agent for a in report.actions]
    assert agent_names == ["triage", "investigator", "escalation"]


def test_process_batch_preserves_order():
    orchestrator = Orchestrator()
    tickets = [make_ticket(id=f"T-{i}", title="x", body="x") for i in range(5)]

    reports = orchestrator.process_batch(tickets)

    assert [r.ticket.id for r in reports] == [t.id for t in tickets]

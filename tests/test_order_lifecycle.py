"""Tests for the synthetic order lifecycle transition policy."""

from agentops.order_lifecycle import evaluate_transition


def test_valid_transition_returns_expected_next_status():
    decision = evaluate_transition("created", "confirm")
    assert decision.allowed
    assert decision.next_status == "CONFIRMED"


def test_out_of_order_shipment_is_rejected():
    decision = evaluate_transition("CONFIRMED", "SHIP")
    assert not decision.allowed
    assert decision.next_status is None
    assert "not valid" in decision.reason


def test_unknown_status_fails_closed():
    decision = evaluate_transition("IN_FLIGHT", "DELIVER")
    assert not decision.allowed
    assert decision.next_status is None
    assert "Unknown order status" in decision.reason


def test_unknown_event_fails_closed():
    decision = evaluate_transition("CREATED", "MAGIC")
    assert not decision.allowed
    assert decision.next_status is None
    assert "Unknown order event" in decision.reason


def test_terminal_status_cannot_transition():
    decision = evaluate_transition("CANCELLED", "CONFIRM")
    assert not decision.allowed
    assert decision.next_status is None
    assert "terminal" in decision.reason


def test_whitespace_and_case_are_normalized():
    decision = evaluate_transition(" created ", " confirm ")
    assert decision.allowed
    assert decision.current_status == "CREATED"
    assert decision.event == "CONFIRM"


def test_return_flow():
    assert evaluate_transition("DELIVERED", "REQUEST_RETURN").next_status == "RETURN_REQUESTED"
    assert evaluate_transition("RETURN_REQUESTED", "COMPLETE_RETURN").next_status == "RETURNED"

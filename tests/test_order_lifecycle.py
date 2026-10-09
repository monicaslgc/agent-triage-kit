"""Tests for deterministic lifecycle, idempotency, and version policy."""

import json
from pathlib import Path

from agentops.order_lifecycle import evaluate_order_event, evaluate_transition


def test_valid_transition_returns_expected_next_status():
    decision = evaluate_transition("created", "confirm")
    assert decision.allowed
    assert decision.next_status == "CONFIRMED"
    assert decision.decision == "ALLOWED"


def test_out_of_order_shipment_is_rejected():
    decision = evaluate_transition("CONFIRMED", "SHIP")
    assert not decision.allowed
    assert decision.next_status is None
    assert "not valid" in decision.reason
    assert decision.decision == "BLOCKED_INVALID_TRANSITION"


def test_unknown_status_fails_closed():
    decision = evaluate_transition("IN_FLIGHT", "DELIVER")
    assert not decision.allowed
    assert decision.next_status is None
    assert decision.decision == "NEEDS_REVIEW_UNKNOWN_VALUE"


def test_unknown_event_fails_closed():
    decision = evaluate_transition("CREATED", "MAGIC")
    assert not decision.allowed
    assert decision.next_status is None
    assert decision.decision == "NEEDS_REVIEW_UNKNOWN_VALUE"


def test_terminal_status_cannot_transition():
    decision = evaluate_transition("CANCELLED", "CONFIRM")
    assert not decision.allowed
    assert decision.next_status is None
    assert decision.decision == "BLOCKED_INVALID_TRANSITION"


def test_whitespace_and_case_are_normalized():
    decision = evaluate_transition(" created ", " confirm ")
    assert decision.allowed
    assert decision.current_status == "CREATED"
    assert decision.event == "CONFIRM"


def test_return_flow():
    assert evaluate_transition("DELIVERED", "REQUEST_RETURN").next_status == "RETURN_REQUESTED"
    assert evaluate_transition("RETURN_REQUESTED", "COMPLETE_RETURN").next_status == "RETURNED"


def test_new_event_with_matching_version_is_allowed_and_proposes_next_version():
    decision = evaluate_order_event(
        "CREATED", "CONFIRM", event_id="evt-001",
        processed_event_ids=set(), expected_version=4, current_version=4,
    )
    assert decision.allowed
    assert decision.decision == "ALLOWED"
    assert decision.next_status == "CONFIRMED"
    assert decision.next_version == 5
    assert decision.event_id == "evt-001"
    assert decision.current_version == 4


def test_duplicate_event_is_ignored_without_proposing_state_change():
    decision = evaluate_order_event(
        "CONFIRMED", "CONFIRM", event_id="evt-already-seen",
        processed_event_ids={"evt-already-seen"}, expected_version=3, current_version=4,
    )
    assert not decision.allowed
    assert decision.decision == "DUPLICATE_EVENT"
    assert decision.next_status is None
    assert decision.next_version == 4
    assert not decision.requires_human_review


def test_duplicate_detection_precedes_stale_version_check():
    decision = evaluate_order_event(
        "CONFIRMED", "CONFIRM", event_id="evt-retry",
        processed_event_ids={"evt-retry"}, expected_version=2, current_version=5,
    )
    assert decision.decision == "DUPLICATE_EVENT"


def test_stale_version_is_blocked_for_a_new_event():
    decision = evaluate_order_event(
        "CREATED", "CONFIRM", event_id="evt-002",
        processed_event_ids=set(), expected_version=2, current_version=3,
    )
    assert not decision.allowed
    assert decision.decision == "VERSION_CONFLICT"
    assert decision.next_status is None
    assert decision.next_version is None
    assert decision.requires_human_review


def test_invalid_transition_does_not_propose_version_increment():
    decision = evaluate_order_event(
        "CONFIRMED", "SHIP", event_id="evt-003",
        processed_event_ids=set(), expected_version=7, current_version=7,
    )
    assert decision.decision == "BLOCKED_INVALID_TRANSITION"
    assert decision.next_version is None


def test_missing_event_id_requires_review():
    decision = evaluate_order_event(
        "CREATED", "CONFIRM", event_id=" ",
        processed_event_ids=set(), expected_version=0, current_version=0,
    )
    assert decision.decision == "INVALID_INPUT"
    assert decision.requires_human_review
    assert decision.next_status is None


def test_negative_version_requires_review():
    decision = evaluate_order_event(
        "CREATED", "CONFIRM", event_id="evt-004",
        processed_event_ids=set(), expected_version=-1, current_version=0,
    )
    assert decision.decision == "INVALID_INPUT"
    assert decision.requires_human_review


def test_synthetic_fixture_decisions_match_expected_results():
    fixture_path = (
        Path(__file__).resolve().parents[1]
        / "examples"
        / "order-lifecycle-consistency"
        / "orders.json"
    )
    examples = json.loads(fixture_path.read_text(encoding="utf-8"))

    for example in examples:
        result = evaluate_order_event(
            example["current_status"],
            example["event"],
            event_id=example["event_id"],
            processed_event_ids=example["processed_event_ids"],
            expected_version=example["expected_version"],
            current_version=example["current_version"],
        )
        assert result.decision == example["expected_decision"], example["order_id"]
        assert result.next_status == example["expected_next_status"], example["order_id"]

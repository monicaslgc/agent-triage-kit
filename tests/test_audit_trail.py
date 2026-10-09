"""Tests for immutable audit records and human-review recording."""
from dataclasses import FrozenInstanceError, asdict

import pytest

from agentops.audit_trail import create_audit_record, record_human_review
from agentops.order_lifecycle import evaluate_order_event, evaluate_transition


def _decision(requires_review=False):
    if requires_review:
        return evaluate_order_event(
            "CREATED", "CONFIRM", event_id="evt-review",
            processed_event_ids=set(), expected_version=1, current_version=2,
        )
    return evaluate_order_event(
        "CREATED", "CONFIRM", event_id="evt-ok",
        processed_event_ids=set(), expected_version=2, current_version=2,
    )


def _record(requires_review=True):
    return create_audit_record(
        _decision(requires_review),
        audit_id="audit-001",
        order_id="DEMO-1001",
        recorded_at="2026-10-09T12:00:00Z",
        correlation_id="corr-001",
    )


def test_allowed_decision_creates_audit_record_without_review():
    record = _record(False)
    payload = asdict(record)
    assert payload["schema_version"] == 1
    assert payload["decision"] == "ALLOWED"
    assert payload["next_status"] == "CONFIRMED"
    assert payload["review_status"] == "NOT_REQUIRED"
    assert payload["requires_human_review"] is False


def test_review_required_decision_starts_pending():
    record = _record(True)
    assert record.decision == "VERSION_CONFLICT"
    assert record.review_status == "PENDING"
    assert record.requires_human_review
    assert record.next_status is None


def test_human_approval_records_disposition_but_does_not_apply_transition():
    original = _record(True)
    reviewed = record_human_review(
        original, reviewer_id="reviewer-01", outcome="APPROVE",
        reviewed_at="2026-10-09T12:05:00Z", note="Reviewed source version; reconcile before retry.",
    )
    assert reviewed.review_status == "APPROVED"
    assert reviewed.review_outcome == "APPROVE"
    assert reviewed.next_status is None
    assert reviewed.decision == "VERSION_CONFLICT"
    assert original.review_status == "PENDING"


def test_human_rejection_is_recorded():
    reviewed = record_human_review(
        _record(), reviewer_id="reviewer-02", outcome="REJECT",
        reviewed_at="2026-10-09T12:06:00Z", note="Source-of-truth mismatch remains unresolved.",
    )
    assert reviewed.review_status == "REJECTED"
    assert reviewed.review_outcome == "REJECT"


def test_cannot_review_record_that_does_not_require_review():
    with pytest.raises(ValueError, match="not awaiting review"):
        record_human_review(
            _record(False), reviewer_id="reviewer-01", outcome="APPROVE",
            reviewed_at="2026-10-09T12:05:00Z", note="No review required.",
        )


@pytest.mark.parametrize("field,value", [
    ("audit_id", ""), ("order_id", " "), ("recorded_at", ""), ("actor", " "),
])
def test_required_audit_metadata_cannot_be_blank(field, value):
    kwargs = dict(audit_id="audit-002", order_id="DEMO-1002",
                  recorded_at="2026-10-09T12:00:00Z", actor="policy-engine")
    kwargs[field] = value
    with pytest.raises(ValueError, match="Required audit fields"):
        create_audit_record(_decision(), **kwargs)


def test_review_requires_reviewer_timestamp_and_note():
    with pytest.raises(ValueError, match="reviewer_id"):
        record_human_review(_record(), reviewer_id=" ", outcome="APPROVE",
                            reviewed_at="2026-10-09T12:05:00Z", note="Reviewed.")
    with pytest.raises(ValueError, match="reviewed_at"):
        record_human_review(_record(), reviewer_id="reviewer-01", outcome="APPROVE",
                            reviewed_at=" ", note="Reviewed.")
    with pytest.raises(ValueError, match="review note"):
        record_human_review(_record(), reviewer_id="reviewer-01", outcome="APPROVE",
                            reviewed_at="2026-10-09T12:05:00Z", note=" ")


def test_audit_record_is_immutable():
    record = _record()
    with pytest.raises(FrozenInstanceError):
        record.review_status = "APPROVED"


def test_invalid_transition_is_still_audited_as_a_decision():
    decision = evaluate_transition("CONFIRMED", "SHIP")
    record = create_audit_record(
        decision, audit_id="audit-003", order_id="DEMO-1003",
        recorded_at="2026-10-09T12:00:00Z",
    )
    assert record.decision == "BLOCKED_INVALID_TRANSITION"
    assert record.review_status == "NOT_REQUIRED"
    assert record.next_status is None

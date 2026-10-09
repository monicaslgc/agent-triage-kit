"""Structured audit records and explicit human-review decisions.

This is a deterministic portfolio demo. It does not persist records, mutate
orders, or apply approved transitions; callers own durable storage and commits.
"""
from dataclasses import dataclass, replace
from typing import Literal

from agentops.order_lifecycle import TransitionDecision

ReviewStatus = Literal["NOT_REQUIRED", "PENDING", "APPROVED", "REJECTED"]
ReviewOutcome = Literal["APPROVE", "REJECT"]


@dataclass(frozen=True)
class AuditRecord:
    """Immutable record of a policy decision and any subsequent human review."""

    schema_version: int
    audit_id: str
    order_id: str
    event_id: str | None
    correlation_id: str | None
    recorded_at: str
    actor: str
    decision: str
    reason: str
    allowed: bool
    current_status: str
    event: str
    next_status: str | None
    expected_version: int | None
    current_version: int | None
    next_version: int | None
    requires_human_review: bool
    review_status: ReviewStatus
    reviewer_id: str | None = None
    review_outcome: ReviewOutcome | None = None
    review_note: str | None = None
    reviewed_at: str | None = None


def create_audit_record(
    decision: TransitionDecision,
    *,
    audit_id: str,
    order_id: str,
    recorded_at: str,
    correlation_id: str | None = None,
    actor: str = "policy-engine",
) -> AuditRecord:
    """Create a stable, serializable audit record from an evaluated decision.

    Timestamps and identifiers are supplied by the caller so this function
    stays deterministic and does not invent identity or time information.
    """
    required = {
        "audit_id": audit_id,
        "order_id": order_id,
        "recorded_at": recorded_at,
        "actor": actor,
    }
    missing = [key for key, value in required.items() if not isinstance(value, str) or not value.strip()]
    if missing:
        raise ValueError(f"Required audit fields missing or blank: {', '.join(missing)}")

    review_status: ReviewStatus = "PENDING" if decision.requires_human_review else "NOT_REQUIRED"
    return AuditRecord(
        schema_version=1,
        audit_id=audit_id,
        order_id=order_id,
        event_id=decision.event_id,
        correlation_id=correlation_id,
        recorded_at=recorded_at,
        actor=actor,
        decision=decision.decision,
        reason=decision.reason,
        allowed=decision.allowed,
        current_status=decision.current_status,
        event=decision.event,
        next_status=decision.next_status,
        expected_version=decision.expected_version,
        current_version=decision.current_version,
        next_version=decision.next_version,
        requires_human_review=decision.requires_human_review,
        review_status=review_status,
    )


def record_human_review(
    record: AuditRecord,
    *,
    reviewer_id: str,
    outcome: ReviewOutcome,
    reviewed_at: str,
    note: str,
) -> AuditRecord:
    """Record a human disposition without applying or changing the order.

    Only records awaiting review may be reviewed. A review outcome is evidence
    of a human decision, not permission for this demo to perform side effects.
    """
    if record.review_status != "PENDING":
        raise ValueError(f"Record is not awaiting review: {record.review_status}")
    if not isinstance(reviewer_id, str) or not reviewer_id.strip():
        raise ValueError("reviewer_id must be a non-empty string")
    if outcome not in ("APPROVE", "REJECT"):
        raise ValueError("outcome must be APPROVE or REJECT")
    if not isinstance(reviewed_at, str) or not reviewed_at.strip():
        raise ValueError("reviewed_at must be a non-empty string")
    if not isinstance(note, str) or not note.strip():
        raise ValueError("A non-empty review note is required")

    return replace(
        record,
        review_status="APPROVED" if outcome == "APPROVE" else "REJECTED",
        reviewer_id=reviewer_id,
        review_outcome=outcome,
        review_note=note,
        reviewed_at=reviewed_at,
    )

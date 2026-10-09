"""Deterministic order lifecycle policy for a synthetic portfolio demo.

This module evaluates proposed events only. It never persists state, calls
external systems, or performs payment, fulfilment, or other side effects.
"""

from dataclasses import dataclass
from typing import Collection, Final


TRANSITIONS: Final[dict[tuple[str, str], str]] = {
    ("CREATED", "CONFIRM"): "CONFIRMED",
    ("CREATED", "CANCEL"): "CANCELLED",
    ("CONFIRMED", "START_PROCESSING"): "PROCESSING",
    ("CONFIRMED", "CANCEL"): "CANCELLED",
    ("PROCESSING", "SHIP"): "SHIPPED",
    ("PROCESSING", "CANCEL"): "CANCELLED",
    ("SHIPPED", "DELIVER"): "DELIVERED",
    ("DELIVERED", "REQUEST_RETURN"): "RETURN_REQUESTED",
    ("RETURN_REQUESTED", "COMPLETE_RETURN"): "RETURNED",
}

KNOWN_STATUSES: Final[frozenset[str]] = frozenset(
    {
        "CREATED", "CONFIRMED", "PROCESSING", "SHIPPED",
        "DELIVERED", "CANCELLED", "RETURN_REQUESTED", "RETURNED",
    }
)
KNOWN_EVENTS: Final[frozenset[str]] = frozenset(event for _, event in TRANSITIONS)
TERMINAL_STATUSES: Final[frozenset[str]] = frozenset({"CANCELLED", "RETURNED"})


@dataclass(frozen=True)
class TransitionDecision:
    """Explainable result of evaluating an event; no order is mutated."""

    allowed: bool
    current_status: str
    event: str
    next_status: str | None
    reason: str
    decision: str = "ALLOWED"
    event_id: str | None = None
    expected_version: int | None = None
    current_version: int | None = None
    next_version: int | None = None
    requires_human_review: bool = False


def _normalize(value: object) -> str:
    return value.strip().upper() if isinstance(value, str) else ""


def evaluate_transition(current_status: str, event: str) -> TransitionDecision:
    """Validate a status/event pair against the explicit transition policy."""
    status = _normalize(current_status)
    normalized_event = _normalize(event)

    if status not in KNOWN_STATUSES:
        return TransitionDecision(
            False, status, normalized_event, None,
            f"Unknown order status: {status or '<empty>'}",
            decision="NEEDS_REVIEW_UNKNOWN_VALUE", requires_human_review=True,
        )

    if normalized_event not in KNOWN_EVENTS:
        return TransitionDecision(
            False, status, normalized_event, None,
            f"Unknown order event: {normalized_event or '<empty>'}",
            decision="NEEDS_REVIEW_UNKNOWN_VALUE", requires_human_review=True,
        )

    if status in TERMINAL_STATUSES:
        return TransitionDecision(
            False, status, normalized_event, None,
            f"{status} is a terminal status; no further transitions are allowed",
            decision="BLOCKED_INVALID_TRANSITION",
        )

    next_status = TRANSITIONS.get((status, normalized_event))
    if next_status is None:
        return TransitionDecision(
            False, status, normalized_event, None,
            f"Event {normalized_event} is not valid while order is {status}",
            decision="BLOCKED_INVALID_TRANSITION",
        )

    return TransitionDecision(
        True, status, normalized_event, next_status,
        f"Allowed transition: {status} -> {next_status}",
        decision="ALLOWED",
    )


def evaluate_order_event(
    current_status: str,
    event: str,
    *,
    event_id: str,
    processed_event_ids: Collection[str],
    expected_version: int,
    current_version: int,
) -> TransitionDecision:
    """Check idempotency and optimistic concurrency before transition policy.

    Duplicate event IDs are treated as safe no-ops before version comparison:
    retries of an already-processed event must not be applied a second time.
    A new event with a stale expected version is blocked. This function does
    not record event IDs or increment persisted versions; the caller must do
    that atomically only after an approved decision is committed.
    """
    status = _normalize(current_status)
    normalized_event = _normalize(event)

    if not isinstance(event_id, str) or not event_id.strip():
        return TransitionDecision(
            False, status, normalized_event, None,
            "Missing event_id; idempotency cannot be evaluated safely",
            decision="INVALID_INPUT", requires_human_review=True,
        )

    if (
        isinstance(expected_version, bool)
        or not isinstance(expected_version, int)
        or expected_version < 0
        or isinstance(current_version, bool)
        or not isinstance(current_version, int)
        or current_version < 0
    ):
        return TransitionDecision(
            False, status, normalized_event, None,
            "Order versions must be non-negative integers",
            decision="INVALID_INPUT", event_id=event_id,
            requires_human_review=True,
        )

    if event_id in processed_event_ids:
        return TransitionDecision(
            False, status, normalized_event, None,
            f"Event {event_id} was already processed; duplicate ignored",
            decision="DUPLICATE_EVENT", event_id=event_id,
            expected_version=expected_version, current_version=current_version,
            next_version=current_version,
        )

    if expected_version != current_version:
        return TransitionDecision(
            False, status, normalized_event, None,
            f"Version conflict: expected {expected_version}, current version is {current_version}",
            decision="VERSION_CONFLICT", event_id=event_id,
            expected_version=expected_version, current_version=current_version,
            requires_human_review=True,
        )

    transition = evaluate_transition(status, normalized_event)
    return TransitionDecision(
        allowed=transition.allowed,
        current_status=transition.current_status,
        event=transition.event,
        next_status=transition.next_status,
        reason=transition.reason,
        decision=transition.decision,
        event_id=event_id,
        expected_version=expected_version,
        current_version=current_version,
        next_version=current_version + 1 if transition.allowed else None,
        requires_human_review=transition.requires_human_review,
    )

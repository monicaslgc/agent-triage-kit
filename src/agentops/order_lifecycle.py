"""Deterministic order state-transition policy for a synthetic portfolio demo.

This module evaluates transitions only. It deliberately performs no persistence,
network calls, payment actions, fulfilment actions, or AI-based policy decisions.
"""

from dataclasses import dataclass
from typing import Final


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
        "CREATED",
        "CONFIRMED",
        "PROCESSING",
        "SHIPPED",
        "DELIVERED",
        "CANCELLED",
        "RETURN_REQUESTED",
        "RETURNED",
    }
)
KNOWN_EVENTS: Final[frozenset[str]] = frozenset(event for _, event in TRANSITIONS)
TERMINAL_STATUSES: Final[frozenset[str]] = frozenset({"CANCELLED", "RETURNED"})


@dataclass(frozen=True)
class TransitionDecision:
    """Explainable result of evaluating one proposed order event."""

    allowed: bool
    current_status: str
    event: str
    next_status: str | None
    reason: str


def evaluate_transition(current_status: str, event: str) -> TransitionDecision:
    """Evaluate a proposed event without mutating order state.

    Inputs are normalized to uppercase to tolerate casing differences. Unknown
    values and transitions fail closed; callers must not infer permission from
    missing or unexpected data.
    """
    status = current_status.strip().upper()
    normalized_event = event.strip().upper()

    if status not in KNOWN_STATUSES:
        return TransitionDecision(
            False, status, normalized_event, None,
            f"Unknown order status: {status or '<empty>'}",
        )

    if normalized_event not in KNOWN_EVENTS:
        return TransitionDecision(
            False, status, normalized_event, None,
            f"Unknown order event: {normalized_event or '<empty>'}",
        )

    if status in TERMINAL_STATUSES:
        return TransitionDecision(
            False, status, normalized_event, None,
            f"{status} is a terminal status; no further transitions are allowed",
        )

    next_status = TRANSITIONS.get((status, normalized_event))
    if next_status is None:
        return TransitionDecision(
            False, status, normalized_event, None,
            f"Event {normalized_event} is not valid while order is {status}",
        )

    return TransitionDecision(
        True,
        status,
        normalized_event,
        next_status,
        f"Allowed transition: {status} -> {next_status}",
    )

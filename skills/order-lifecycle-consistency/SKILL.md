---
name: order-lifecycle-consistency
description: Evaluate order status/event combinations against an explicit lifecycle policy, explain invalid transitions, and identify cases that require human review. Use for synthetic order-workflow analysis and test-case generation; never assume access to a live commerce system.
---

# Order Lifecycle Consistency Skill

## Purpose

Help a product, operations, or engineering team reason about order lifecycle events and identify state inconsistencies before downstream actions are taken.

This skill is a portfolio artifact. It is not a live integration and does not describe any employer's internal system.

## Required inputs

For each order event, collect:

- `order_id`: synthetic or appropriately authorized identifier
- `current_status`: the state reported by the source of truth
- `event`: the event being proposed or received
- `event_id` and `order_version`, when available, for future idempotency/concurrency checks

If required fields are missing or ambiguous, ask for clarification or mark the case as `NEEDS_REVIEW`. Do not infer a missing status.

## Procedure

1. Normalize status and event casing/whitespace for comparison only.
2. Check that the status and event belong to the known policy vocabulary.
3. Look up the exact pair `(current_status, event)` in the approved transition table.
4. Return one of:
   - `ALLOWED`: transition exists and a next status is defined.
   - `BLOCKED_INVALID_TRANSITION`: known event is not allowed from this status.
   - `NEEDS_REVIEW_UNKNOWN_VALUE`: status or event is unknown or missing.
5. Explain the decision using the current status, event, expected next status (if any), and reason.
6. Recommend that a downstream system or authorized human perform any actual state change. This skill only evaluates; it must not claim to have updated an order.

## Safety and reliability rules

- Never invent a valid transition.
- Never override deterministic business rules with an LLM guess.
- Never trigger payment, cancellation, shipment, refund, or customer communication.
- Treat duplicate events and concurrent updates as unresolved until idempotency and version-check rules are explicitly specified.
- Escalate conflicting source-of-truth data to an authorized human.
- Use synthetic data in portfolio examples; do not include real customer, order, or employer-confidential information.

## Output contract

Return structured fields:

```json
{
  "order_id": "DEMO-1001",
  "decision": "ALLOWED",
  "current_status": "CREATED",
  "event": "CONFIRM",
  "next_status": "CONFIRMED",
  "reason": "Allowed transition: CREATED -> CONFIRMED",
  "requires_human_review": false
}
```

## Evaluation examples

- `CREATED + CONFIRM` -> `ALLOWED`, next status `CONFIRMED`.
- `CONFIRMED + SHIP` -> `BLOCKED_INVALID_TRANSITION`; processing must start first.
- `CANCELLED + CONFIRM` -> `BLOCKED_INVALID_TRANSITION`; terminal state.
- Unknown status -> `NEEDS_REVIEW_UNKNOWN_VALUE`, with no next status.

If the approved transition table changes, update the tests and documentation together before using the new policy.

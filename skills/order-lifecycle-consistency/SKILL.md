---
name: order-lifecycle-consistency
description: Evaluate order status/event combinations against an explicit lifecycle policy, detect duplicate event IDs, identify stale-version conflicts, and explain when human review is required. Use for synthetic order-workflow analysis and test-case generation; never assume access to a live commerce system.
---

# Order Lifecycle Consistency Skill

## Purpose

Help product, operations, and engineering teams reason about order lifecycle events and detect unsafe state changes before a downstream service or authorized person acts.

This is an original portfolio artifact using synthetic examples. It is not a live integration and does not describe an employer's internal system.

## Required inputs

For a proposed event, provide:

- `order_id`: synthetic or appropriately authorized identifier
- `current_status`: status from the designated source of truth
- `event`: proposed event
- `event_id`: stable unique identifier used to recognize retries
- `processed_event_ids`: IDs already recorded as processed for this order
- `expected_version`: order version observed by the event producer
- `current_version`: latest order version read by the evaluator

Missing event IDs or invalid versions must produce `INVALID_INPUT` and require review. Never invent an identifier or version.

## Evaluation procedure

1. Normalize status and event casing/whitespace for comparison.
2. Validate that the event ID is present and both versions are non-negative integers.
3. Check whether the event ID has already been processed. If so, return `DUPLICATE_EVENT` as a no-op. Duplicate detection takes precedence over version comparison so a retried event is not misclassified just because its original version is now stale.
4. For a new event, compare `expected_version` with `current_version`. A mismatch returns `VERSION_CONFLICT`, blocks the proposed transition, and requires human or caller-side reconciliation.
5. Validate the exact `(current_status, event)` pair against the approved transition table.
6. Return a structured decision and reason. Never claim that state has actually changed.

## Decision values

- `ALLOWED`: event is valid for this status and the expected version matches. `next_version` proposes the version after a successful commit.
- `BLOCKED_INVALID_TRANSITION`: known event is not allowed from the current status.
- `NEEDS_REVIEW_UNKNOWN_VALUE`: status or event is unknown.
- `DUPLICATE_EVENT`: event ID was already processed; treat as a no-op.
- `VERSION_CONFLICT`: the producer's expected version is stale.
- `INVALID_INPUT`: event ID or version metadata is missing or invalid.

## Output contract

Return structured fields:

```json
{
  "order_id": "DEMO-1001",
  "decision": "ALLOWED",
  "event_id": "evt-1001",
  "current_status": "CREATED",
  "event": "CONFIRM",
  "next_status": "CONFIRMED",
  "expected_version": 4,
  "current_version": 4,
  "next_version": 5,
  "requires_human_review": false,
  "reason": "Allowed transition: CREATED -> CONFIRMED"
}
```

For `DUPLICATE_EVENT`, return no next status and do not propose another version increment. For `VERSION_CONFLICT`, return no next status and set `requires_human_review=true`.

## Reliability boundaries

- This evaluator is a pure decision function. It does not persist an event ledger, mutate orders, increment stored versions, or call external systems.
- A production caller must atomically check-and-record the event ID and commit the state/version update. An in-memory list or pre-read alone cannot guarantee idempotency across concurrent workers or processes.
- Never override deterministic policy with an LLM guess.
- Never trigger payment, cancellation, shipment, refund, or customer communication.
- Escalate conflicting source-of-truth data to an authorized human.
- Use synthetic data in portfolio examples; do not include real customer, order, or employer-confidential information.

## Synthetic evaluation cases

- `CREATED + CONFIRM`, matching version -> `ALLOWED`, next status `CONFIRMED`.
- `CONFIRMED + SHIP`, matching version -> `BLOCKED_INVALID_TRANSITION`.
- Previously processed event ID -> `DUPLICATE_EVENT`, no state change.
- New event with stale expected version -> `VERSION_CONFLICT`, human review required.
- Missing event ID or negative version -> `INVALID_INPUT`.
- Unknown status or event -> `NEEDS_REVIEW_UNKNOWN_VALUE`.

If the approved transition table changes, update the tests, fixtures, diagrams, and documentation together before using the new policy.

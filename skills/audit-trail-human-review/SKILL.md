---
name: audit-trail-human-review
description: Create structured audit records for deterministic workflow decisions and record explicit human review outcomes. Use when decisions need traceability, review ownership, and a non-side-effecting approval/rejection record.
---

# Audit Trail + Human Review Workflow Skill

## Purpose

Turn a deterministic workflow decision into an immutable, structured audit record and, where the policy explicitly requires it, capture a human reviewer’s disposition. This is a synthetic portfolio demonstration, not a live integration.

## Required inputs

For audit creation, provide the policy decision plus non-empty `audit_id`, `order_id`, and `recorded_at`. An optional `correlation_id` connects related events, and `actor` identifies the component that evaluated the decision. Do not invent identifiers, timestamps, reviewer identities, or outcomes.

For review, provide a record in `PENDING`, a non-empty `reviewer_id`, an explicit `APPROVE` or `REJECT` outcome, a non-empty `reviewed_at`, and a note explaining the rationale.

## Workflow

1. Evaluate the event with the deterministic lifecycle policy.
2. Record the decision, reason, order/event identifiers, statuses, versions, and whether review is required.
3. Set `review_status=PENDING` only when the policy decision explicitly requires human review; otherwise use `NOT_REQUIRED`.
4. A reviewer can record `APPROVE` or `REJECT` only while the record is pending.
5. Preserve the original policy decision. Human review updates review metadata; it does not change `decision`, synthesize a `next_status`, or execute the proposed transition.
6. Persist records and any order updates only in an external system with appropriate authorization and atomicity. This demo is in-memory and side-effect-free.

## Audit record contract

Fields include `schema_version`, `audit_id`, `order_id`, `event_id`, `correlation_id`, `recorded_at`, `actor`, `decision`, `reason`, `allowed`, `current_status`, `event`, `next_status`, version fields, `requires_human_review`, `review_status`, and optional reviewer/outcome/note/timestamp fields.

## Safety boundaries

- Never interpret human approval as automatic authorization for payment, cancellation, shipment, refund, or customer communication.
- A version conflict is not resolved merely because someone clicks approve; the caller must reconcile the authoritative state and re-evaluate the event.
- Do not overwrite the original decision or delete the audit trail.
- Production audit storage needs durable retention, access controls, integrity protections, privacy review, and defined retention policies.
- Use only synthetic identifiers and timestamps in portfolio fixtures.

## Synthetic examples

- `ALLOWED` -> audit record with `NOT_REQUIRED`.
- `VERSION_CONFLICT` -> audit record with `PENDING`.
- Human `APPROVE` -> review metadata becomes `APPROVED`, but the original decision stays `VERSION_CONFLICT` and no next status is added.
- Human `REJECT` -> review metadata becomes `REJECTED`, with the original decision preserved.

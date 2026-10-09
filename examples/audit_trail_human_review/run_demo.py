"""Run the synthetic audit trail and human-review demonstration."""
from dataclasses import asdict
import json

from agentops.audit_trail import create_audit_record, record_human_review
from agentops.order_lifecycle import evaluate_order_event


def main() -> None:
    decision = evaluate_order_event(
        "CREATED", "CONFIRM", event_id="evt-demo-101",
        processed_event_ids=set(), expected_version=3, current_version=4,
    )
    record = create_audit_record(
        decision, audit_id="audit-demo-101", order_id="DEMO-101",
        recorded_at="2026-10-09T12:00:00Z", correlation_id="corr-demo-101",
    )
    print("PENDING REVIEW")
    print(json.dumps(asdict(record), indent=2))

    reviewed = record_human_review(
        record, reviewer_id="synthetic-reviewer-01", outcome="REJECT",
        reviewed_at="2026-10-09T12:10:00Z",
        note="Version conflict must be reconciled against the source of truth.",
    )
    print("\nREVIEW RECORDED (no order mutation)")
    print(json.dumps(asdict(reviewed), indent=2))


if __name__ == "__main__":
    main()

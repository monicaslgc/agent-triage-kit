"""Run synthetic lifecycle, duplicate-event, and version-conflict scenarios."""

import json
from pathlib import Path

from agentops.order_lifecycle import evaluate_order_event


def main() -> None:
    data_path = Path(__file__).resolve().parents[1] / "order-lifecycle-consistency" / "orders.json"
    examples = json.loads(data_path.read_text(encoding="utf-8"))
    failures = 0

    for example in examples:
        decision = evaluate_order_event(
            example["current_status"],
            example["event"],
            event_id=example["event_id"],
            processed_event_ids=example["processed_event_ids"],
            expected_version=example["expected_version"],
            current_version=example["current_version"],
        )
        passed = (
            decision.decision == example["expected_decision"]
            and decision.next_status == example["expected_next_status"]
        )
        failures += not passed
        print(
            f'{example["order_id"]}: {decision.decision} | '
            f'status={decision.current_status} | event={decision.event} | '
            f'next={decision.next_status or "-"} | '
            f'version={decision.current_version}->{decision.next_version or "-"} | '
            f'check={"PASS" if passed else "FAIL"} | {decision.reason}'
        )

    if failures:
        raise SystemExit(f"{failures} synthetic scenario(s) failed")


if __name__ == "__main__":
    main()

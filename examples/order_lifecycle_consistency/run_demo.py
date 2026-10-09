"""Run the synthetic order lifecycle examples from orders.json."""

import json
from pathlib import Path

from agentops.order_lifecycle import evaluate_transition


def main() -> None:
    data_path = Path(__file__).resolve().parents[1] / "order-lifecycle-consistency" / "orders.json"
    examples = json.loads(data_path.read_text(encoding="utf-8"))

    for example in examples:
        decision = evaluate_transition(
            example["current_status"],
            example["event"],
        )
        print(
            f'{example["order_id"]}: {decision.current_status} + {decision.event} '
            f'-> {decision.next_status or "BLOCKED"} | '
            f'allowed={decision.allowed} | {decision.reason}'
        )


if __name__ == "__main__":
    main()

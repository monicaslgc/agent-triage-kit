"""Tests for the synthetic order lifecycle transition policy."""

import unittest

from examples.order_lifecycle_consistency.order_lifecycle import evaluate_transition


class EvaluateTransitionTests(unittest.TestCase):
    def test_valid_transition_returns_expected_next_status(self):
        decision = evaluate_transition("created", "confirm")
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.next_status, "CONFIRMED")

    def test_out_of_order_shipment_is_rejected(self):
        decision = evaluate_transition("CONFIRMED", "SHIP")
        self.assertFalse(decision.allowed)
        self.assertIsNone(decision.next_status)
        self.assertIn("not valid", decision.reason)

    def test_unknown_status_fails_closed(self):
        decision = evaluate_transition("IN_FLIGHT", "DELIVER")
        self.assertFalse(decision.allowed)
        self.assertIsNone(decision.next_status)
        self.assertIn("Unknown order status", decision.reason)

    def test_unknown_event_fails_closed(self):
        decision = evaluate_transition("CREATED", "MAGIC")
        self.assertFalse(decision.allowed)
        self.assertIsNone(decision.next_status)
        self.assertIn("Unknown order event", decision.reason)

    def test_terminal_status_cannot_transition(self):
        decision = evaluate_transition("CANCELLED", "CONFIRM")
        self.assertFalse(decision.allowed)
        self.assertIsNone(decision.next_status)
        self.assertIn("terminal", decision.reason)

    def test_whitespace_and_case_are_normalized(self):
        decision = evaluate_transition(" created ", " confirm ")
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.current_status, "CREATED")
        self.assertEqual(decision.event, "CONFIRM")

    def test_return_flow(self):
        self.assertEqual(
            evaluate_transition("DELIVERED", "REQUEST_RETURN").next_status,
            "RETURN_REQUESTED",
        )
        self.assertEqual(
            evaluate_transition("RETURN_REQUESTED", "COMPLETE_RETURN").next_status,
            "RETURNED",
        )


if __name__ == "__main__":
    unittest.main()

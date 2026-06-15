"""Unit tests for heuristic planner classification.

Run pass/fail checks (no math output):
    python -m unittest tests.test_planner -v

See scores, tiebreak, and confidence math step-by-step:
    python -m services.planner --trace "How do I cancel and get a refund?"
"""

from __future__ import annotations

import unittest

from services.planner import classify_workflow, compute_confidence


class PlannerClassificationTests(unittest.TestCase):
    def assert_classification(
        self,
        message: str,
        *,
        policy_domain: str,
        intent: str,
        workflow_type: str,
    ) -> None:
        result = classify_workflow(message)
        self.assertEqual(result["policy_domain"], policy_domain, msg=message)
        self.assertEqual(result["intent"], intent, msg=message)
        self.assertEqual(result["workflow_type"], workflow_type, msg=message)

    # --- Core eval-aligned paths ---

    def test_return_action_with_order(self) -> None:
        self.assert_classification(
            "Can I return order PG-1001?",
            policy_domain="returns",
            intent="action",
            workflow_type="returns_request",
        )

    def test_return_policy_question(self) -> None:
        self.assert_classification(
            "What is your return policy?",
            policy_domain="returns",
            intent="policy",
            workflow_type="returns_policy",
        )

    def test_shipping_status_request(self) -> None:
        self.assert_classification(
            "Where is order PG-1002?",
            policy_domain="shipping",
            intent="action",
            workflow_type="shipping_request",
        )

    def test_cancellation_request(self) -> None:
        self.assert_classification(
            "Can I cancel order PG-1010?",
            policy_domain="cancellation",
            intent="action",
            workflow_type="cancellation_request",
        )

    def test_damaged_action(self) -> None:
        self.assert_classification(
            "My order PG-1001 arrived broken",
            policy_domain="damaged_items",
            intent="action",
            workflow_type="damaged_items_request",
        )

    def test_damaged_policy(self) -> None:
        self.assert_classification(
            "what happens if my order arrives damaged?",
            policy_domain="damaged_items",
            intent="policy",
            workflow_type="damaged_items_policy",
        )

    def test_missing_package_action(self) -> None:
        self.assert_classification(
            "My order PG-1001 never arrived",
            policy_domain="missing_package",
            intent="action",
            workflow_type="missing_package_request",
        )

    def test_missing_package_policy(self) -> None:
        self.assert_classification(
            "what happens if my order says delivered but is missing?",
            policy_domain="missing_package",
            intent="policy",
            workflow_type="missing_package_policy",
        )

    def test_faqs_always_policy_workflow(self) -> None:
        self.assert_classification(
            "I want to know the company's mission",
            policy_domain="faqs",
            intent="action",
            workflow_type="faqs_policy",
        )

    def test_unsupported_out_of_scope(self) -> None:
        self.assert_classification(
            "Can you reset my Netflix password?",
            policy_domain="unsupported",
            intent="policy",
            workflow_type="unsupported",
        )

    # --- Tiebreak and overlap fixes ---

    def test_tracking_delivered_routes_to_missing_package(self) -> None:
        self.assert_classification(
            "My order never came but tracking says delivered",
            policy_domain="missing_package",
            intent="action",
            workflow_type="missing_package_request",
        )

    def test_stop_shipment_routes_to_cancellation(self) -> None:
        self.assert_classification(
            "Stop shipment on PG-1002",
            policy_domain="cancellation",
            intent="action",
            workflow_type="cancellation_request",
        )

    def test_cancel_and_refund_prefers_cancellation(self) -> None:
        self.assert_classification(
            "How do I cancel and get a refund?",
            policy_domain="cancellation",
            intent="action",
            workflow_type="cancellation_request",
        )

    def test_broken_item_prefers_damaged_over_returns(self) -> None:
        self.assert_classification(
            "My item is broken and I want a refund for PG-1001",
            policy_domain="damaged_items",
            intent="action",
            workflow_type="damaged_items_request",
        )

    def test_porch_theft_missing_package(self) -> None:
        self.assert_classification(
            "Package stolen from porch says delivered",
            policy_domain="missing_package",
            intent="action",
            workflow_type="missing_package_request",
        )

    def test_combined_return_shipping_policy_question(self) -> None:
        self.assert_classification(
            "My order is 1234, what is your return and shipping policy?",
            policy_domain="returns",
            intent="policy",
            workflow_type="returns_policy",
        )

    # --- Confidence and metadata ---

    def test_high_confidence_clear_return(self) -> None:
        result = classify_workflow("Can I return order PG-1001?")
        self.assertGreaterEqual(result["confidence"], 0.67)
        self.assertFalse(result["ambiguous"])

    def test_unsupported_has_zero_confidence(self) -> None:
        result = classify_workflow("Can you reset my Netflix password?")
        self.assertEqual(result["confidence"], 0.0)
        self.assertEqual(result["policy_domain"], "unsupported")

    def test_tiebreak_flag_set_on_overlap(self) -> None:
        result = classify_workflow("How do I cancel and get a refund?")
        self.assertTrue(result["tiebreak_applied"])
        self.assertEqual(result["policy_domain"], "cancellation")
        self.assertFalse(result["ambiguous"])

    def test_order_id_extraction(self) -> None:
        result = classify_workflow("Can I return order PG-2048?")
        self.assertEqual(result["order_id"], "PG-2048")

    def test_missing_order_id_on_action(self) -> None:
        result = classify_workflow("I want to return my order.")
        self.assertEqual(result["missing_fields"], ["order_id"])
        self.assertTrue(result["requires_order"])


class ComputeConfidenceTests(unittest.TestCase):
    THRESHOLD = 0.67

    def _llm_would_run(self, top: int, second: int, tied_at_top: bool, tiebreak: bool) -> bool:
        confidence = compute_confidence(top, second, tied_at_top)
        if tiebreak:
            confidence = max(confidence, self.THRESHOLD)
        return confidence < self.THRESHOLD

    def test_bucket_no_hits(self) -> None:
        self.assertEqual(compute_confidence(0, 0, False), 0.0)
        self.assertTrue(self._llm_would_run(0, 0, False, False))

    def test_bucket_sole_domain_one_hit(self) -> None:
        self.assertEqual(compute_confidence(1, 0, False), 0.67)
        self.assertFalse(self._llm_would_run(1, 0, False, False))

    def test_bucket_sole_domain_multi_hit(self) -> None:
        self.assertEqual(compute_confidence(2, 0, False), 1.0)
        self.assertFalse(self._llm_would_run(2, 0, False, False))

    def test_bucket_weak_winner(self) -> None:
        self.assertEqual(compute_confidence(2, 1, False), 0.33)
        self.assertTrue(self._llm_would_run(2, 1, False, False))

    def test_bucket_solid_lead(self) -> None:
        self.assertEqual(compute_confidence(3, 1, False), 0.67)
        self.assertFalse(self._llm_would_run(3, 1, False, False))

    def test_bucket_narrow_lead(self) -> None:
        self.assertEqual(compute_confidence(3, 2, False), 0.33)
        self.assertTrue(self._llm_would_run(3, 2, False, False))

    def test_bucket_tie_at_top(self) -> None:
        self.assertEqual(compute_confidence(1, 1, True), 0.0)
        self.assertFalse(self._llm_would_run(1, 1, True, True))

    def test_unsupported_opens_llm_gate(self) -> None:
        result = classify_workflow("Can you reset my Netflix password?")
        self.assertLess(result["confidence"], self.THRESHOLD)

    def test_tiebreak_closes_llm_gate(self) -> None:
        result = classify_workflow("How do I cancel and get a refund?")
        self.assertGreaterEqual(result["confidence"], self.THRESHOLD)


if __name__ == "__main__":
    unittest.main()

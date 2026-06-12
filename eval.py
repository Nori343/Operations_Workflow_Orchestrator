from workflow_graph import workflow_app
from schemas import SupportTicket
from schemas import WorkflowState

EVAL_CASES = [
    {
        "name": "approved_return",
        "message": "Can I return order PG-1001?",
        "expected": {
            "workflow_type": "returns_request",
            "decision": "approved",
            "recommended_action": "explain_return_approved",
        },
    },
    {
        "name": "return_before_delivery",
        "message": "Can I return order PG-1003?",
        "expected": {
            "workflow_type": "returns_request",
            "decision": "denied",
            "recommended_action": "explain_non_returnable_status",
        },
    },
    {
        "name": "return_already_returned",
        "message": "Can I return order PG-1005 again?",
        "expected": {
            "workflow_type": "returns_request",
            "decision": "denied",
            "recommended_action": "explain_non_returnable_status",
        },
    },
    {
        "name": "return_clearance_item",
        "message": "Can I return order PG-1004?",
        "expected": {
            "workflow_type": "returns_request",
            "decision": "denied",
            "recommended_action": "explain_non_eligible_items",
        },
    },
    {
        "name": "shipping_status_shipped",
        "message": "Where is order PG-1002?",
        "expected": {
            "workflow_type": "shipping_request",
            "decision": "provide_shipping_status",
            "recommended_action": "generate_response",
        },
    },
    {
        "name": "shipping_status_processing",
        "message": "Where is order PG-1003?",
        "expected": {
            "workflow_type": "shipping_request",
            "decision": "provide_shipping_status",
            "recommended_action": "generate_response",
        },
    },
    {
        "name": "shipping_eta_request",
        "message": "When will order PG-1007 arrive?",
        "expected": {
            "workflow_type": "shipping_request",
            "decision": "provide_shipping_status",
            "recommended_action": "generate_response",
        },
    },
    {
        "name": "cancellation_within_window",
        "message": "Can I cancel order PG-1010?",
        "expected": {
            "workflow_type": "cancellation_request",
            "decision": "approved_with_fee",
            "recommended_action": "cancel_order_with_fee",
        },
    },
    {
        "name": "cancellation_past_window_shipped",
        "message": "Can I cancel order PG-1002?",
        "expected": {
            "workflow_type": "cancellation_request",
            "decision": "denied",
            "recommended_action": "explain_cannot_cancel_shipped_order",
        },
    },
    {
        "name": "policy_only_return_question",
        "message": "What is your return policy?",
        "expected": {
            "workflow_type": "returns_policy",
            "decision": "explain_general_returns_policy",
            "recommended_action": "generate_response",
        },
    },
    {
        "name": "missing_order_id_return",
        "message": "I want to return my order.",
        "expected": {
            "workflow_type": "returns_request",
            "decision": "needs_more_info",
            "recommended_action": "request_order_id",
        },
    },
    {
        "name": "unsupported_question",
        "message": "Can you reset my Netflix password?",
        "expected": {
            "workflow_type": "unsupported",
            "decision": "explain_general_unsupported_policy",
            "recommended_action": "generate_response",
        },
    },
    {
        "name": "damaged_policy",
        "message": "what happens if my order arrives damaged?",
        "expected": {
            "workflow_type": "damaged_items_policy",
            "decision": "explain_general_damaged_items_policy",
            "recommended_action": "generate_response",
        },
    },
        {
        "name": "item_damaged",
        "message": "My order PG-1001 arrived broken",
        "expected": {
            "workflow_type": "damaged_items_request",
            "decision": "denied",
            "recommended_action": "explain_outside_damaged_report_window",
        },
    },
    {
        "name": "missing_policy",
        "message": "what happens if my order says delivered but is missing?",
        "expected": {
            "workflow_type": "missing_package_policy",
            "decision": "explain_general_missing_package_policy",
            "recommended_action": "generate_response",
        },
    },
    {
        "name": "missing_package",
        "message": "My order PG-1001 never arrived",
        "expected": {
            "workflow_type": "missing_package_request",
            "decision": "approved",
            "recommended_action": "explain_missing_package_refund_approved",
        },
    }
]


# ====================== EVALUATION LOOP ======================

for i, case in enumerate(EVAL_CASES):
    print(f"\n{'=' * 75}")
    print(f"RUNNING: {case['name']}")
    print(f"Message: {case['message']}")

    result = workflow_app.invoke({
        "ticket_id": f"eval_{i}",
        "customer_message": case["message"]
    })

    policy_decision = result.get("policy_decision") or {}
    risk_decision = result.get("risk_decision") or {}

    print(f"Workflow Type     : {result.get('workflow_type')}")
    print(f"Decision          : {policy_decision.get('decision')}")
    print(f"Recommended Action: {policy_decision.get('recommended_action')}")
    print(f"Risk Decision : {risk_decision}")
    print(f"Response Preview  : {result.get('response')[:350]}...\n")

    try:
        assert result.get("workflow_type") == case["expected"]["workflow_type"], \
            f"Wrong workflow_type. Expected: {case['expected']['workflow_type']}"

        assert policy_decision.get("decision") == case["expected"]["decision"], \
            f"Wrong decision. Expected: {case['expected']['decision']}"

        if "recommended_action" in case["expected"]:
            assert policy_decision.get("recommended_action") == case["expected"]["recommended_action"], \
                f"Wrong recommended_action. Expected: {case['expected']['recommended_action']}"

        print(f"✅ {case['name']} PASSED")

    except AssertionError as e:
        print(f"❌ {case['name']} FAILED: {e}")
    except Exception as e:
        print(f"❌ {case['name']} ERROR: {e}")
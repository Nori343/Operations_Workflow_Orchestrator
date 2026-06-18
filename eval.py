from langchain_core.messages import HumanMessage

from config.settings import settings
from graph.builder import workflow_app

EVAL_CASES = [
    {
        "name": "approved_return",
        "message": "Can I return order PG-1001?",
        "expected": {
            "workflow_type": "returns_request",
            "planner_source": "heuristic",
            "decision": "approved",
            "recommended_action": "explain_return_approved",
        },
    },
    {
        "name": "return_before_delivery",
        "message": "Can I return order PG-1003?",
        "expected": {
            "workflow_type": "returns_request",
            "planner_source": "heuristic",
            "decision": "denied",
            "recommended_action": "explain_non_returnable_status",
        },
    },
    {
        "name": "return_already_returned",
        "message": "Can I return order PG-1005 again?",
        "expected": {
            "workflow_type": "returns_request",
            "planner_source": "heuristic",
            "decision": "denied",
            "recommended_action": "explain_non_returnable_status",
        },
    },
    {
        "name": "return_clearance_item",
        "message": "Can I return order PG-1004?",
        "expected": {
            "workflow_type": "returns_request",
            "planner_source": "heuristic",
            "decision": "denied",
            "recommended_action": "explain_non_eligible_items",
        },
    },
    {
        "name": "shipping_status_shipped",
        "message": "Where is order PG-1002?",
        "expected": {
            "workflow_type": "shipping_request",
            "planner_source": "heuristic",
            "decision": "provide_shipping_status",
            "recommended_action": "explain_order_shipped",
        },
    },
    {
        "name": "shipping_status_processing",
        "message": "Where is order PG-1003?",
        "expected": {
            "workflow_type": "shipping_request",
            "planner_source": "heuristic",
            "decision": "provide_shipping_status",
            "recommended_action": "explain_order_processing",
        },
    },
    {
        "name": "shipping_eta_request",
        "message": "When will order PG-1007 arrive?",
        "expected": {
            "workflow_type": "shipping_request",
            "planner_source": "heuristic",
            "decision": "provide_shipping_status",
            "recommended_action": "explain_order_shipped",
        },
    },
    {
        "name": "cancellation_within_window",
        "message": "Can I cancel order PG-1010?",
        "expected": {
            "workflow_type": "cancellation_request",
            "planner_source": "heuristic",
            "decision": "approved_with_fee",
            "recommended_action": "cancel_order_with_fee",
        },
    },
    {
        "name": "cancellation_past_window_shipped",
        "message": "Can I cancel order PG-1002?",
        "expected": {
            "workflow_type": "cancellation_request",
            "planner_source": "heuristic",
            "decision": "denied",
            "recommended_action": "explain_cannot_cancel_shipped_order",
        },
    },
    {
        "name": "policy_only_return_question",
        "message": "What is your return policy?",
        "expected": {
            "workflow_type": "returns_policy",
            "planner_source": "heuristic",
            "decision": "explain_general_returns_policy",
            "recommended_action": "generate_response",
        },
    },
    {
        "name": "missing_order_id_return",
        "message": "I want to return my order.",
        "expected": {
            "workflow_type": "returns_request",
            "planner_source": "heuristic",
            "decision": "needs_more_info",
            "recommended_action": "request_order_id",
        },
    },
    {
        "name": "unsupported_question",
        "message": "Can you reset my Netflix password?",
        "expected": {
            "workflow_type": "unsupported",
            "planner_source": "llm",
            "decision": "explain_general_unsupported_policy",
            "recommended_action": "generate_response",
        },
    },
    {
        "name": "damaged_policy",
        "message": "what happens if my order arrives damaged?",
        "expected": {
            "workflow_type": "damaged_items_policy",
            "planner_source": "heuristic",
            "decision": "explain_general_damaged_items_policy",
            "recommended_action": "generate_response",
        },
    },
    {
        "name": "item_damaged",
        "message": "My order PG-1001 arrived broken",
        "expected": {
            "workflow_type": "damaged_items_request",
            "planner_source": "heuristic",
            "decision": "denied",
            "recommended_action": "explain_outside_damaged_report_window",
        },
    },
    {
        "name": "missing_policy",
        "message": "what happens if my order says delivered but is missing?",
        "expected": {
            "workflow_type": "missing_package_policy",
            "planner_source": "heuristic",
            "decision": "explain_general_missing_package_policy",
            "recommended_action": "generate_response",
        },
    },
    {
        "name": "missing_package",
        "message": "My order PG-1001 never arrived",
        "expected": {
            "workflow_type": "missing_package_request",
            "planner_source": "heuristic",
            "decision": "open_carrier_investigation",
            "recommended_action": "carrier_investigation_open",
        },
    },
    {
        "name": "faqs_policy",
        "message": "When was the company founded",
        "expected": {
            "workflow_type": "faqs_policy",
            "planner_source": "heuristic",
            "decision": "explain_general_faqs_policy",
            "recommended_action": "generate_response",
        },
    },
    {
        "name": "faqs_request",
        "message": "I want to know the company's mission",
        "expected": {
            "workflow_type": "faqs_policy",
            "planner_source": "heuristic",
            "decision": "explain_general_faqs_policy",
            "recommended_action": "generate_response",
        },
    },
    {
        "name": "ambiguous_undo",
        "message": "I want to undo my purchase",
        "expected": {
            "workflow_type": "cancellation_request",
            "planner_source": "llm",
            "decision": "needs_more_info",
            "recommended_action": "request_order_id",
        },
    },
    {
        "name": "ambiguous_with_order",
        "message": "My order arrived smashed, its PG-1001 can i get a new one?",
        "expected": {
            "workflow_type": "damaged_items_request",
            "planner_source": "heuristic",
            "decision": "denied",
            "recommended_action": "explain_outside_damaged_report_window",
        },
    },
    {
        "name": "tiebreak",
        "message": "How do i cancel and get a refund?",
        "expected": {
            "workflow_type": "cancellation_request",
            "planner_source": "heuristic",
            "decision": "needs_more_info",
            "recommended_action": "request_order_id",
        },
    },
]

MULTITURN_EVAL_CASES = [
    {
        "name": "multiturn_return_supply_order_id",
        "turns": [
            {
                "message": "I want to return my order.",
                "expected": {
                    "workflow_type": "returns_request",
                    "planner_source": "heuristic",
                    "decision": "needs_more_info",
                    "recommended_action": "request_order_id",
                    "missing_fields": ["order_id"],
                },
            },
            {
                "message": "PG-1001",
                "expected": {
                    "workflow_type": "returns_request",
                    "planner_source": "continuation",
                    "decision": "approved",
                    "recommended_action": "explain_return_approved",
                    "order_id": "PG-1001",
                },
            },
        ],
    },
    {
        "name": "multiturn_cancellation_supply_order_id",
        "turns": [
            {
                "message": "I want to cancel my order.",
                "expected": {
                    "workflow_type": "cancellation_request",
                    "planner_source": "heuristic",
                    "decision": "needs_more_info",
                    "recommended_action": "request_order_id",
                    "missing_fields": ["order_id"],
                },
            },
            {
                "message": "PG-1010",
                "expected": {
                    "workflow_type": "cancellation_request",
                    "planner_source": "continuation",
                    "decision": "approved_with_fee",
                    "recommended_action": "cancel_order_with_fee",
                    "order_id": "PG-1010",
                },
            },
        ],
    },
    {
        "name": "multiturn_shipping_supply_order_id",
        "turns": [
            {
                "message": "Where is my order?",
                "expected": {
                    "workflow_type": "shipping_request",
                    "planner_source": "heuristic",
                    "decision": "needs_more_info",
                    "recommended_action": "request_order_id",
                    "missing_fields": ["order_id"],
                },
            },
            {
                "message": "PG-1002",
                "expected": {
                    "workflow_type": "shipping_request",
                    "planner_source": "continuation",
                    "decision": "provide_shipping_status",
                    "recommended_action": "explain_order_shipped",
                    "order_id": "PG-1002",
                },
            },
        ],
    },
    {
        "name": "multiturn_return_still_no_order_id",
        "turns": [
            {
                "message": "I want to return my order.",
                "expected": {
                    "workflow_type": "returns_request",
                    "planner_source": "heuristic",
                    "decision": "needs_more_info",
                    "recommended_action": "request_order_id",
                    "missing_fields": ["order_id"],
                },
            },
            {
                "message": "I still need help with my return",
                "expected": {
                    "workflow_type": "returns_request",
                    "planner_source": "heuristic",
                    "decision": "needs_more_info",
                    "recommended_action": "request_order_id",
                    "missing_fields": ["order_id"],
                },
            },
        ],
    },
    {
        "name": "multiturn_return_then_policy_question",
        "turns": [
            {
                "message": "I want to return my order.",
                "expected": {
                    "workflow_type": "returns_request",
                    "planner_source": "heuristic",
                    "decision": "needs_more_info",
                    "recommended_action": "request_order_id",
                    "missing_fields": ["order_id"],
                },
            },
            {
                "message": "PG-1001",
                "expected": {
                    "workflow_type": "returns_request",
                    "planner_source": "continuation",
                    "decision": "approved",
                    "recommended_action": "explain_return_approved",
                    "order_id": "PG-1001",
                },
            },
            {
                "message": "What is your return window for standard items?",
                "expected": {
                    "workflow_type": "returns_policy",
                    "planner_source": "heuristic",
                    "decision": "explain_general_returns_policy",
                    "recommended_action": "generate_response",
                },
            },
        ],
    },
    {
        "name": "multiturn_missing_package_supply_order_id",
        "turns": [
            {
                "message": "My package never arrived",
                "expected": {
                    "workflow_type": "missing_package_request",
                    "planner_source": "heuristic",
                    "decision": "needs_more_info",
                    "recommended_action": "request_order_id",
                    "missing_fields": ["order_id"],
                },
            },
            {
                "message": "PG-1001",
                "expected": {
                    "workflow_type": "missing_package_request",
                    "planner_source": "continuation",
                    "decision": "open_carrier_investigation",
                    "recommended_action": "carrier_investigation_open",
                    "order_id": "PG-1001",
                },
            },
        ],
    },
]


def _print_result(result: dict) -> None:
    policy_decision = result.get("policy_decision") or {}
    risk_decision = result.get("risk_decision") or {}

    print(f"Workflow Type     : {result.get('workflow_type')}")
    print(f"Planner Source    : {result.get('planner_source')}")
    print(f"Order ID          : {result.get('order_id')}")
    print(f"Missing Fields    : {result.get('missing_fields')}")
    print(f"Decision          : {policy_decision.get('decision')}")
    print(f"Recommended Action: {policy_decision.get('recommended_action')}")
    print(f"Risk Decision     : {risk_decision}")
    response = result.get("response") or ""
    print(f"Response Preview  : {response[:350]}...\n")


def _assert_expected(result: dict, expected: dict, label: str) -> None:
    policy_decision = result.get("policy_decision") or {}

    assert result.get("workflow_type") == expected["workflow_type"], (
        f"{label}: wrong workflow_type. Expected: {expected['workflow_type']}"
    )

    assert policy_decision.get("decision") == expected["decision"], (
        f"{label}: wrong decision. Expected: {expected['decision']}"
    )

    if "recommended_action" in expected:
        assert policy_decision.get("recommended_action") == expected["recommended_action"], (
            f"{label}: wrong recommended_action. Expected: {expected['recommended_action']}"
        )

    if "missing_fields" in expected:
        assert result.get("missing_fields") == expected["missing_fields"], (
            f"{label}: wrong missing_fields. Expected: {expected['missing_fields']}"
        )

    if "order_id" in expected:
        assert result.get("order_id") == expected["order_id"], (
            f"{label}: wrong order_id. Expected: {expected['order_id']}"
        )

    expected_source = expected["planner_source"]
    if expected_source == "llm" and not settings.llm.is_available:
        print(f"  ({label}: skipped planner_source check — no OPENAI_API_KEY)")
    else:
        assert result.get("planner_source") == expected_source, (
            f"{label}: wrong planner_source. Expected: {expected_source}"
        )


def _invoke_turn(message: str, thread_id: str) -> dict:
    return workflow_app.invoke(
        {
            "customer_message": message,
            "messages": [HumanMessage(content=message)],
        },
        config={"configurable": {"thread_id": thread_id}},
    )


def run_evals() -> None:
    for case in EVAL_CASES:
        print(f"\n{'=' * 75}")
        print(f"RUNNING: {case['name']}")
        print(f"Message: {case['message']}")

        result = _invoke_turn(case["message"], f"eval-{case['name']}")

        _print_result(result)

        try:
            _assert_expected(result, case["expected"], case["name"])
            print(f"✅ {case['name']} PASSED")

        except AssertionError as e:
            print(f"❌ {case['name']} FAILED: {e}")
        except Exception as e:
            print(f"❌ {case['name']} ERROR: {e}")

    for case in MULTITURN_EVAL_CASES:
        print(f"\n{'=' * 75}")
        print(f"RUNNING MULTITURN: {case['name']}")
        thread_id = f"eval-multiturn-{case['name']}"
        case_failed = False

        for turn_num, turn in enumerate(case["turns"], start=1):
            print(f"\n--- Turn {turn_num}: {turn['message']!r} ---")
            result = _invoke_turn(turn["message"], thread_id)
            _print_result(result)

            label = f"{case['name']} turn {turn_num}"
            try:
                _assert_expected(result, turn["expected"], label)
                print(f"✅ {label} PASSED")
            except AssertionError as e:
                print(f"❌ {label} FAILED: {e}")
                case_failed = True
                break
            except Exception as e:
                print(f"❌ {label} ERROR: {e}")
                case_failed = True
                break

        if not case_failed:
            print(f"✅ {case['name']} PASSED (all turns)")


if __name__ == "__main__":
    run_evals()

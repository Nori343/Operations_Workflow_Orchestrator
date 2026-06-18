from __future__ import annotations
from services.planner import classify_workflow, planner_output_to_state, try_continue_ticket
from state.workflow_state import WorkflowState

from langchain_core.messages import AIMessage


def _planner_trace_message(result):
    return AIMessage(
        content=(
            f"[planner] source={result.planner_source}"
            f"confidence={result.confidence:.2f} order_id = {result.order_id}"
        )
    )

def planner_node(state: WorkflowState) -> dict:
    try:
        continued = try_continue_ticket(
            customer_message=state.get("customer_message", ""),
            missing_fields=state.get("missing_fields") or [],
            workflow_type=state.get("workflow_type"),
            policy_domain=state.get("policy_domain"),
            intent=state.get("intent"),
            confidence=state.get("confidence", 0.0),
            intent_confidence=state.get("intent_confidence", 0.0),
            matched_terms=state.get("matched_terms") or [],
            candidate_domains=state.get("candidate_domains") or [],
            top_score=state.get("top_score", 0),
            second_score=state.get("second_score", 0),
            tiebreak_applied=state.get("tiebreak_applied", False),
        )
        if continued:
            return {
                **planner_output_to_state(continued),
                "messages": [_planner_trace_message(continued)],
                "node_trace": ["planner"],
            }

        result = classify_workflow(state.get("customer_message", ""))
        return {
            "order": None,
            **planner_output_to_state(result),
           "messages": [_planner_trace_message(result)],
            "node_trace": ["planner"],
        }
    except Exception as e:
      return {
            "workflow_type": "unsupported",
            "policy_domain": "unsupported",
            "missing_fields": [],
            "errors": [f"planner: {e}"],
            "node_trace": ["planner"],
        }
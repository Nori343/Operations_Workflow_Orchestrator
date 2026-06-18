from state.workflow_state import WorkflowState
from workers.handler_registry import HANDLER_REGISTRY, get_handler


def apply_policy(state: WorkflowState) -> dict:
    try:
        handler = get_handler(state.get("workflow_type"))
        return handler(state)
    except Exception as e:
        return {
            "policy_decision": {
                "decision": "error",
                "recommended_action": "generate_response",
                "reason": "An internal error occurred evaluating policy.",
            },
            "errors": [f"policy: {e}"],
        }
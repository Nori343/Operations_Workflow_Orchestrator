from services.llm import craft_response
from state.workflow_state import WorkflowState


def response_node(state: WorkflowState) -> dict:
    try:
        return {**craft_response(state), "node_trace": ["response"]}
    except Exception as exc:
        return {
            "response": "Thank you for contacting support due to an internal error we cannot help you at this time. Please check back later.",
            "errors": [f"response: {exc}"],
            "node_trace": ["response"],
        }

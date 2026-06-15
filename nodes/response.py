from services.llm import craft_response
from state.workflow_state import WorkflowState


def response_node(state: WorkflowState) -> dict:
    return {**craft_response(state), "node_trace": ["response"]}

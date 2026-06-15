from services.planner import classify_workflow
from state.workflow_state import WorkflowState


def planner_node(state: WorkflowState) -> dict:
    return {
        **classify_workflow(state.get("customer_message", "")),
        "node_trace": ["planner"],
    }

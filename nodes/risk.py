from workers.risk_worker import measure_risk
from state.workflow_state import WorkflowState


def risk_node(state: WorkflowState) -> dict:
    return {**measure_risk(state), "node_trace": ["risk"]}

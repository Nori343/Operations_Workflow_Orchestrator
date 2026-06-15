from workers.order_worker import lookup_order
from state.workflow_state import WorkflowState


def order_node(state: WorkflowState) -> dict:
    return {**lookup_order(state), "node_trace": ["order"]}

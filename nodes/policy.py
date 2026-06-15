from workers.policy_worker import apply_policy
from state.workflow_state import WorkflowState


def policy_node(state: WorkflowState) -> dict:
    return {**apply_policy(state), "node_trace": ["policy"]}

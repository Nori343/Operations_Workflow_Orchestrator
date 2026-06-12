from schemas import WorkflowState
from workers.handler_registry import HANDLER_REGISTRY, get_handler


def apply_policy(state: WorkflowState) -> WorkflowState:
    handler  = get_handler(state.workflow_type)
    return handler(state)

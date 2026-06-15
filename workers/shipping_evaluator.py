from schemas import PolicyDecision
from state.workflow_state import WorkflowState
from data.policy_store import POLICIES

def evaluate_shipping(state: WorkflowState) -> dict:
    policy = POLICIES.get(state.get("policy_domain"))
    order = state.get("order")
    
    if order is None:
        decision = PolicyDecision(
            decision="shipping_request_no_order",
            recommended_action="request_order_id",
            reason="No order data available for shipping inquiry",
            policy_json=policy
        ).model_dump()
    else:
        decision = PolicyDecision(
            decision="provide_shipping_status",
            recommended_action="generate_response",
            reason="Order-specific shipping status request",
            policy_json=policy
        ).model_dump()
    
    return {
        "policy_decision": decision
    }
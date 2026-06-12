from schemas import WorkflowState, PolicyDecision
from data.policy_store import POLICIES

def evaluate_shipping(state: WorkflowState) -> WorkflowState:   # ← Better name
    policy = POLICIES.get(state.policy_domain, {})
    order = state.order
    
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
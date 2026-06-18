from schemas import RiskDecision
from state.workflow_state import WorkflowState

def measure_risk(state: WorkflowState) -> dict:
    workflow_type = state.get("workflow_type")
    policy_decision = state.get("policy_decision")
    order = state.get("order")

    risk_flags = []
    escalation_required = False
    risk_level = "low"
    reason = "No escalation rule triggered."
    recommended_action = "proceed_with_response"

    if workflow_type == "unsupported":
        escalation_required = True
        recommended_action= "route_to_human_queue"
        risk_level = "medium"
        risk_flags.append("unsupported_workflow")
        reason = "Unsupported workflow type requires human review"
    
    elif workflow_type == "missing_package_request":
        escalation_required = True
        recommended_action= "route_to_human_queue"
        risk_level = "medium"
        risk_flags.append("missing_package_claim")
        reason = "Missing package claim requires human review before refund or replacement"
    
    if order is not None and order.get("total", 0) > 500:
        escalation_required = True
        recommended_action= "route_to_human_queue"
        risk_level = "high"
        risk_flags.append("high_value_order")
        reason = "High-value order requires human review."
    
    return {
        "risk_decision": RiskDecision(
            escalation_required=escalation_required,
            recommended_action=recommended_action,
            risk_level=risk_level,
            reason=reason,
            risk_flags=risk_flags,
        ).model_dump()
    }

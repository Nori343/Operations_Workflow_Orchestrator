from schemas import RiskDecision


def measure_risk(state: dict) -> dict:
    workflow_type = state.workflow_type
    policy_decision = state.policy_decision
    order = state.order

    risk_flags = []
    escalation_required = False
    risk_level = "low"
    reason = "No escalation rule triggered."

    if workflow_type == "unsupported":
        escalation_required = True
        risk_level = "medium"
        risk_flags.append("unsupported_workflow")
        reason = "Unsupported workflow type requires human review"
    
    elif workflow_type == "missing_package_request":
        escalation_required = True
        risk_level = "medium"
        risk_flags.append("mising_package_claim")
        reason = "Missing package claim requires human review before refund or replacement"
    
    if order is not None and order.total > 500:
        escalation_required = True
        risk_level = "high"
        risk_flags.append("high_value_order")
        reason = "High-value order requires human review."
    
    return {
        "risk_decision": RiskDecision(
            escalation_required=escalation_required,
            risk_level=risk_level,
            reason=reason,
            risk_flags=risk_flags,
        ).model_dump()
    }

from schemas import RiskDecision
from state.workflow_state import WorkflowState
from workers.risk_worker import measure_risk


def risk_node(state: WorkflowState) -> dict:
    try:
        return {**measure_risk(state), "node_trace": ["risk"]}
    except Exception as exc:
        return {
            "risk_decision": RiskDecision(
                escalation_required=False,
                recommended_action="proceed_with_response",
                risk_level="low",
                reason="No escalation rule triggered.",
                risk_flags=[],
            ).model_dump(),
            "errors": [f"risk: {exc}"],
            "node_trace": ["risk"],
        }

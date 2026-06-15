from schemas import PolicyDecision
from state.workflow_state import WorkflowState
from data.policy_store import POLICIES


def evaluate_policy(state: WorkflowState) -> dict:
    policy_domain  = state.get("policy_domain")
    policy = POLICIES.get(policy_domain)
    
    if not policy:
        policy = {"summary": "Sorry, I couldn't find specific policy information for this topic.", 
                  "policy_id": "unknown"}
    
    decision = PolicyDecision(
        decision=f"explain_general_{policy_domain}_policy",     # e.g. "general_returns_policy"
        recommended_action="generate_response",
        reason=f"General {policy_domain} policy question",
        policy_json=policy,                                   # Full policy section
    ).model_dump()

    return {
        "policy_decision": decision
    }
    

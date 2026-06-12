from schemas import PolicyDecision
from schemas import PolicyDecision, WorkflowState
from data.policy_store import POLICIES



def evaluate_policy(state: WorkflowState) -> WorkflowState: #handler for policy queries of all domains
    policy = POLICIES.get(state.policy_domain, {})
    
    if not policy:
        policy = {"summary": "Sorry, I couldn't find specific policy information for this topic.", 
                  "policy_id": "unknown"}
    
    decision = PolicyDecision(
        decision=f"explain_general_{state.policy_domain}_policy",     # e.g. "general_returns_policy"
        recommended_action="generate_response",
        reason=f"General {state.policy_domain} policy question",
        policy_json=policy,                                   # Full policy section
    ).model_dump()

    return {
        "policy_decision": decision
    }
    

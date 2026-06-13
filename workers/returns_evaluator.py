from schemas import Order, PolicyDecision
from state.workflow_state import WorkflowState
from datetime import datetime, timedelta
from data.policy_store import POLICIES

def check_return_window(order:dict, window_days:int): #check window for returns for an order
        delivered_at = order.get("delivered_at")
        if not delivered_at:
             return False
        try:
            if isinstance(delivered_at, str):
                dt = datetime.fromisoformat(delivered_at)
            else:
                dt = delivered_at
            now = datetime.now().date()
            return_deadline = dt + timedelta(days=window_days)
            is_within_return_window = now <= return_deadline.date()
            return is_within_return_window
        except (ValueError, TypeError, AttributeError) as e:
            print(f"Warning: Could not parse return window for order {order.get('order_id')}: {e}")
            return False 
        
def evaluate_returns_eligibility(order: Order, rules: dict) -> dict:
    """
    Evaluates return eligibility using policy rules.
    Returns structured decision data.
    """
    # Default happy path
    result = {
        "decision": "approved",
        "recommended_action": "explain_return_approved",
        "reason": "Order is eligible for return",
        "next_steps": []
    }

    # 1. Status Check
    if order.get("status") in rules.get("non_returnable_statuses", []):
        result.update({
            "decision": "denied",
            "recommended_action": "explain_non_returnable_status",
            "reason": rules["denial_reasons"]["invalid_status"]
        })
        return result

    # 2. Clearance / Custom Check
    if order.get("contains_clearance_items") or order.get("contains_custom_items"):
        result.update({
            "decision": "denied",
            "recommended_action": "explain_non_eligible_items",
            "reason": rules["denial_reasons"]["non_returnable_item"]
        })
        return result

    # 3. Return Window Check
    window_days = rules["premium_window_days"] if order.get("is_premium_member") else rules["standard_window_days"]
    
    if not check_return_window(order, window_days):
        result.update({
            "decision": "denied",
            "recommended_action": "explain_past_return_window",
            "reason": rules["denial_reasons"]["past_return_window"]
        })
        return result

    # Approved
    result["next_steps"] = rules.get("customer_steps", [])
    return result

def evaluate_returns(state: WorkflowState) -> WorkflowState:
    """Thin handler: loads policy and delegates decision to evaluator"""
    policy = POLICIES.get("returns", {})
    rules = policy.get("structured_rules", {})
    
    if not state.get("order"):
        decision = PolicyDecision(
            decision="needs_more_info",
            recommended_action="request_order_id",
            reason="To assist with your return request, please provide your order number (PG-XXXX).",
            policy_summary=policy.get("summary")
        ).model_dump()
    else:
        # Delegate to evaluator
        evaluation = evaluate_returns_eligibility(state.get("order"), rules)
        
        # Build final PolicyDecision
        decision = PolicyDecision(
            decision=evaluation["decision"],
            recommended_action=evaluation["recommended_action"],
            reason=evaluation["reason"],
            policy_summary=policy.get("summary"),
            policy_sources=[policy.get("policy_id")],
            next_steps=evaluation.get("next_steps", []),
            policy_json=policy
        ).model_dump()
        
    return {
            "policy_decision": decision
        }
from datetime import datetime, timedelta

from config.clock import reference_today
from data.policy_store import POLICIES
from schemas import PolicyDecision
from state.workflow_state import WorkflowState


def check_damaged_window(order: dict, window_days: int) -> bool:
    delivered_at = order.get("delivered_at")
    if not delivered_at:
        return False
    try:
        if isinstance(delivered_at, str):
            dt = datetime.fromisoformat(delivered_at)
        else:
            dt = delivered_at
        deadline = dt.date() + timedelta(days=window_days)
        return reference_today() <= deadline
    except (ValueError, TypeError, AttributeError):
        return False
    
def evaluate_damaged(state: WorkflowState) -> dict:
    policy = POLICIES.get(state.get("policy_domain"), {})
    structured_rules = policy.get("structured_rules", {})
    order = state.get("order")
    if not order:
        decision = PolicyDecision(
        decision="needs_more_info",     
        recommended_action="request_order_id",
        reason="To process request a valid order id is needed"
        ).model_dump()
    else:
        if order.get("status") != "delivered":
            decision = PolicyDecision(
            decision="denied",     
            recommended_action="explain_non_eligible_status",
            reason="Only delivered items can be assessed for damage",
            policy_json=policy,
            ).model_dump()

        elif not check_damaged_window(order, structured_rules.get("report_window_days", 7)):
            decision = PolicyDecision(
            decision="denied",     
            recommended_action="explain_outside_damaged_report_window",
            reason="Damaged items must be reported within 7 days of delivery",
            policy_json=policy,
            ).model_dump()
        elif not state.get("has_damage_photo"):
            decision= PolicyDecision(
            decision = "needs_more_info",     
            recommended_action="request_photo_of_damaged_item",
            reason="Damaged items require a photo to be processed",
            next_steps=policy.get("customer_steps", []),
            policy_json=policy,
            ).model_dump()
        elif state.get("photo_review_status") == "denied":
            decision= PolicyDecision(
            decision = "denied",     
            recommended_action="explain_photo_review_denied",
            reason="Damaged photos are inspected by humans for authenticity",
            policy_json=policy,
            ).model_dump()
        elif state.get("photo_review_status") == "under_review":
            decision= PolicyDecision(
            decision = "under_review",     
            recommended_action="explain_photo_under_review",
            reason="Damaged photos are inspected by humans for authenticity",
            policy_json=policy,
            ).model_dump()
        else:
            decision= PolicyDecision(
            decision="approved",     
            recommended_action="explain_damaged_item_return_approved",
            reason="Damaged items eligible for return"
            ).model_dump()
    return {
        "policy_decision": decision
    }
        



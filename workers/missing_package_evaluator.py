from data.policy_store import POLICIES
from datetime import datetime, timedelta
from schemas import Order, PolicyDecision

{
  "missing_package": {
    "policy_id": "missing_package_v1",
    "version": "1.0",
    "last_updated": "2026-05-30",
    "summary": "If package shows delivered but not received, wait 2 days then contact support. We will investigate and reship or refund if lost.",
    "structured_rules": {
      "wait_days_after_delivery_scan": 2,
      "investigation_days": "3-5",
      "high_value_threshold": 150,
      "high_value_priority": True,
      "resolution_options": ["reship_at_no_cost", "full_refund"]
    },
    "customer_steps": [
      "Wait 2 business days after delivered scan",
      "Check with neighbors, apartment office, or porch camera",
      "Contact support with order number"
    ],
    "cross_references": ["shipping"]
  }}


def check_missing_window(order: Order, window_days: int) -> bool:
    if not order.delivered_at:
        return False
    try:
        if isinstance(order.delivered_at, str):
            dt = datetime.fromisoformat(order.delivered_at)
        else:
            dt = order.delivered_at
        deadline = dt.date() + timedelta(days=window_days)
        return datetime.now().date() > deadline
    except (ValueError, TypeError, AttributeError):
        return False

def evaluate_missing_package(state):
    policy = POLICIES.get(state.policy_domain, {})
    if not state.order:
        decision = PolicyDecision(
        decision="needs_more_info",     
        recommended_action="request_order_id",
        reason="To process request a valid order id is needed"
        ).model_dump()
    else:
        if not check_missing_window(state.order, policy["structured_rules"]["wait_days_after_delivery_scan"]):
            decision = PolicyDecision(
            decision="wait_to_escalate",     
            recommended_action="explain_to_wait_and_look_for_package",
            next_steps=policy["customer_steps"],
            reason="Before carrier investigation wait two days after delivery scan and search for package"
            ).model_dump()
        elif not check_missing_window(state.order, 7):
            decision = PolicyDecision(
            decision="investigate_carrier",     
            recommended_action="explain_wait_for_carrier_investigation",
            reason=f"wait {policy["structured_rules"]["investigation_days"]} days for company to investigate carrier"
            ).model_dump()
        else:
            decision = PolicyDecision(
            decision="approved",     
            recommended_action="explain_missing_package_refund_approved",
            reason="Local and carrier investigation failed to find package"
            ).model_dump()
   
    return {
        "policy_decision": decision
    }

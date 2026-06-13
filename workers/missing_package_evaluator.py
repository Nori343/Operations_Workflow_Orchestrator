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
    
def business_days_since(start_date, end_date=None):
    end_date = end_date or datetime.now().date()
    count = 0
    current = start_date
    while current < end_date:
        current += timedelta(days=1)
        if current.weekday() < 5:  # Mon–Fri
            count += 1
    return count

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
            recommended_action="pending_customer_wait",
            next_steps=policy["customer_steps"],
            reason="Before carrier investigation wait two days after delivery scan and search for package"
            ).model_dump()
        elif state.carrier_investigation_status == 'approved':
            decision = PolicyDecision(
            decision="approved",     
            recommended_action="explain_return/replacement_approved",
            reason="Local and carrier investigation failed to find package"
            ).model_dump()
        elif state.carrier_investigation_status == 'pending':
            decision = PolicyDecision(
            decision="investigation_in_progress",     
            recommended_action="explain_carrier_investigation_underway",
            reason="Carrier investigation must occur before refund or replacement"
            ).model_dump()
        elif state.carrier_investigation_status == 'denied':
            decision = PolicyDecision(
            decision="denied",     
            recommended_action="explain_carrier_investigation_found_contradictory_evidence",
            reason="Carrier investigation found package was delivered"
            ).model_dump()      
        elif not state.carrier_investigation_status:
            decision = PolicyDecision(
            decision="open_carrier_investigation",     
            recommended_action="carrier_investigation_open",
            reason=f"wait {policy["structured_rules"]["investigation_days"]} days for company to investigate carrier"
            ).model_dump()
        else:
            decision = PolicyDecision(
            decision="approved",     
            recommended_action="explain_return/replacement_approved",
            reason="Local and carrier investigation failed to find package"
            ).model_dump()
   
    return {
        "policy_decision": decision
    }

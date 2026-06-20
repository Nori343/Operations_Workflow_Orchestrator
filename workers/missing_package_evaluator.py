from config.clock import reference_now, reference_today
from data.policy_store import POLICIES
from datetime import datetime, timedelta
from schemas import PolicyDecision
from state.workflow_state import WorkflowState


def check_missing_window(order: dict, window_days: int) -> bool:
    delivered_at = order.get("delivered_at")
    if not delivered_at:
        return False
    try:
        if isinstance(delivered_at, str):
            dt = datetime.fromisoformat(delivered_at)
        else:
            dt = delivered_at
        deadline = dt.date() + timedelta(days=window_days)
        return reference_today() > deadline
    except (ValueError, TypeError, AttributeError):
        return False
    
def business_days_since(start_date, end_date=None):
    end_date = end_date or reference_today()
    count = 0
    current = start_date
    while current < end_date:
        current += timedelta(days=1)
        if current.weekday() < 5:  # Mon–Fri
            count += 1
    return count

def evaluate_missing_package(state: WorkflowState) -> dict:
    policy = POLICIES.get(state.get("policy_domain"), {})
    structured_rules = policy.get("structured_rules", {})
    order = state.get("order")
    carrier_investigation_status = state.get("carrier_investigation_status")
    if not order:
        decision = PolicyDecision(
        decision="needs_more_info",     
        recommended_action="request_order_id",
        reason="To process request a valid order id is needed"
        ).model_dump()
    else:
        if not check_missing_window(
            order, structured_rules.get("wait_days_after_delivery_scan", 2)
        ):
            decision = PolicyDecision(
            decision="wait_to_escalate",     
            recommended_action="pending_customer_wait",
            next_steps=policy.get("customer_steps", []),
            reason="Before carrier investigation wait two days after delivery scan and search for package"
            ).model_dump()
        elif carrier_investigation_status == 'approved':
            decision = PolicyDecision(
            decision="approved",     
            recommended_action="explain_return_or_replacement_approved",
            reason="Local and carrier investigation failed to find package"
            ).model_dump()
        elif carrier_investigation_status == 'pending':
            decision = PolicyDecision(
            decision="investigation_in_progress",     
            recommended_action="explain_carrier_investigation_underway",
            reason="Carrier investigation must occur before refund or replacement"
            ).model_dump()
        elif carrier_investigation_status == 'denied':
            decision = PolicyDecision(
            decision="denied",     
            recommended_action="explain_carrier_investigation_found_contradictory_evidence",
            reason="Carrier investigation found package was delivered"
            ).model_dump()      
        elif not carrier_investigation_status:
            decision = PolicyDecision(
            decision="open_carrier_investigation",     
            recommended_action="carrier_investigation_open",
            reason=(
                f"wait {structured_rules.get('investigation_days', '3-5')} days "
                "for company to investigate carrier"
            )
            ).model_dump()
        else:
            decision = PolicyDecision(
            decision="approved",     
            recommended_action="explain_return_or_replacement_approved",
            reason="Local and carrier investigation failed to find package"
            ).model_dump()
   
    return {
        "policy_decision": decision
    }

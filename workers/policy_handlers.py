from schemas import PolicyDecision, Order
from datetime import datetime, timedelta
from schemas import PolicyDecision, WorkflowState
from data.policy_store import POLICIES



def policy_handler(state: WorkflowState) -> WorkflowState: #handler for policy queries of all domains
    policy = POLICIES.get(state.policy_domain, {})
    
    if not policy:
        policy = {"summary": "Sorry, I couldn't find specific policy information for this topic.", 
                  "policy_id": "unknown"}
    
    decision = PolicyDecision(
        decision=f"general_{state.policy_domain}_policy",     # e.g. "general_returns_policy"
        recommended_action="generate_response",
        reason=f"General {state.policy_domain} policy question",
        policy_json=policy,                                   # Full policy section
    )
    state.policy_decision = decision.model_dump()
    return state

def check_return_window(order:dict, is_premium:bool, standard_window, premium_window): #check window for returns for an order
        delivered_at = order.delivered_at
        if not delivered_at:
             return False
        try:
            if isinstance(delivered_at, str):
                dt = datetime.strptime(delivered_at, "%Y-%m-%d")
            else:
                dt = delivered_at
            days_allowed = premium_window if is_premium else standard_window
            now = datetime.now().date()
            return_deadline = dt + timedelta(days=days_allowed)
            is_within_return_window = now <= return_deadline.date()
            return is_within_return_window
        except (ValueError, TypeError, AttributeError) as e:
            print(f"Warning: Could not parse return window for order {order.get('order_id')}: {e}")
            return False 

def returns_handler(state: WorkflowState) -> WorkflowState:
    policy = POLICIES.get(state.policy_domain, {})
    order = state.order
    
    if not order:
        decision = PolicyDecision(
            decision="needs_more_info",
            recommended_action="request_order_id",
            reason="Order id is required to process return request",
            policy_summary=policy.get("summary", ""),
            policy_sources=[policy.get("policy_id", "returns_v1")],
            next_steps=["Ask user for order id", "Re-check eligibility after order is fetched"]
        )
        state.policy_decision = decision.model_dump()
        return state

    # Now we can use clean dot notation
    is_premium = getattr(order, 'is_premium_member', False)
    rules = policy.get("structured_rules", {})
    standard_window = rules.get("standard_window_days", 30)
    premium_window = rules.get("premium_window_days", 45)
    
    within_return_window = check_return_window(order, is_premium, standard_window, premium_window)

    # === Main Decision Logic

    if order.status == "returned":
        decision = PolicyDecision(
            decision="denied",
            recommended_action="explain_already_returned",
            reason="Cannot return an item that's already returned",
            policy_summary=policy.get("summary", ""),
            policy_sources=[policy.get("policy_id", "returns_v1")]
        )

    elif order.status != "delivered":
        decision = PolicyDecision(
            decision="denied",
            recommended_action="explain_not_delivered",
            reason="Only delivered orders can be returned",
            policy_summary=policy.get("summary", ""),
            policy_sources=[policy.get("policy_id", "returns_v1")]
        )

    elif order.contains_clearance_items or order.contains_custom_items:
        decision = PolicyDecision(
            decision="denied",
            recommended_action="explain_non_eligible_items",
            reason="Custom items or clearance items are non-returnable",
            policy_summary=policy.get("summary", ""),
            policy_sources=[policy.get("policy_id", "returns_v1")]
        )

    elif not within_return_window:
        decision = PolicyDecision(
            decision="denied",
            recommended_action="explain_return_window_expired",
            reason="Order is outside return window",
            policy_summary=policy.get("summary", ""),
            policy_sources=[policy.get("policy_id", "returns_v1")]
        )

    else:
        # Approved case
        decision = PolicyDecision(
            decision="approved",
            recommended_action="explain_return_approved",
            reason="Order is eligible and within return window",
            policy_summary=policy.get("summary", ""),
            policy_sources=[policy.get("policy_id", "returns_v1")],
            next_steps=[
                "You will receive a return shipping label via email",
                "Ship items back within 14 days",
                "Refund will be processed within 5-7 business days after receipt"
            ]
        )

    state.policy_decision = decision.model_dump()
    return state


def shipping_handler(state: WorkflowState) -> WorkflowState:   # ← Better name
    policy = POLICIES.get(state.policy_domain, {})
    order = state.order
    
    if order is None:
        decision = PolicyDecision(
            decision="shipping_request_no_order",
            recommended_action="request_order_id",
            reason="No order data available for shipping inquiry",
            policy_json=policy
        )
    else:
        decision = PolicyDecision(
            decision="provide_shipping_status",
            recommended_action="generate_response",
            reason="Order-specific shipping status request",
            policy_json=policy
        )
    
    state.policy_decision = decision.model_dump()
    return state


def check_cancellation_window(order: Order) -> bool:
    """
    Returns True if the order is still within the 4-hour cancellation window.
    """
    # Get the ordered_at field
    ordered_at = getattr(order, 'ordered_at', None)
    
    if not ordered_at:
        return False

    try:
        # Parse the exact format from your mock orders: "2026-04-10T09:00:00"
        if isinstance(ordered_at, str):
            dt = datetime.strptime(ordered_at, "%Y-%m-%dT%H:%M:%S")
        else:
            dt = ordered_at

        # Calculate hours since order was placed
        now = datetime.now()
        hours_since_placed = (now - dt).total_seconds() / 3600
        # Check against 4 hour policy window
        return hours_since_placed <= 4

    except (ValueError, TypeError, AttributeError) as e:
        print(f"Warning: Could not parse cancellation window for order {getattr(order, 'order_id', 'unknown')}: {e}")
        return False
    

def cancellation_handler(state: WorkflowState) -> WorkflowState:
    policy = POLICIES.get(state.policy_domain, {})
    order = state.order
    
    if not order:
        decision = PolicyDecision(
            decision="needs_more_info",
            recommended_action="request_order_id",
            reason="Order id is required to process cancellation request",
            policy_summary=policy.get("summary", ""),
            policy_sources=[policy.get("policy_id", "cancellation_v1")],
            next_steps=["Ask user for order id"]
        )
        state.policy_decision = decision.model_dump()
        return state

    # Main business logic - use if / elif for clear priority
    if order.status in ["shipped", "delivered"]:
        decision = PolicyDecision(
            decision="denied",
            recommended_action="cannot_cancel_shipped_order",
            reason="Orders that have already shipped cannot be cancelled",
            policy_summary=policy.get("summary", ""),
            policy_sources=[policy.get("policy_id", "cancellation_v1")]
        )

    elif order.status != "processing":
        decision = PolicyDecision(
            decision="denied",
            recommended_action="cannot_cancel_non_processing_order",
            reason="Only orders in processing status can be cancelled",
            policy_summary=policy.get("summary", ""),
            policy_sources=[policy.get("policy_id", "cancellation_v1")]
        )

    elif check_cancellation_window(order):
        decision = PolicyDecision(
            decision="approved",
            recommended_action="cancel_order",
            reason="Order is within 4-hour full cancellation window",
            policy_summary=policy.get("summary", ""),
            policy_sources=[policy.get("policy_id", "cancellation_v1")]
        )

    else:
        # Past 4 hours but still in processing → fee applies
        decision = PolicyDecision(
            decision="approved_with_fee",
            recommended_action="cancel_order_with_fee",
            reason="Order can be cancelled with 10 percent restocking fee",
            policy_summary=policy.get("summary", ""),
            policy_sources=[policy.get("policy_id", "cancellation_v1")]
        )

    state.policy_decision = decision.model_dump()
    return state

    
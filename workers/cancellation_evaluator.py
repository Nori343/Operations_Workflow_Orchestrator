from schemas import PolicyDecision
from state.workflow_state import WorkflowState
from config.clock import reference_now
from data.policy_store import POLICIES
from datetime import datetime

def check_cancellation_window(order: dict) -> bool:
    """
    Returns True if the order is still within the 4-hour cancellation window.
    """
    # Get the ordered_at field
    ordered_at = order.get("ordered_at")
    
    if not ordered_at:
        return False

    try:
        # Parse the exact format from your mock orders: "2026-04-10T09:00:00"
        if isinstance(ordered_at, str):
            dt = datetime.fromisoformat(ordered_at.replace("Z", "+00:00")[:19])
        else:
            dt = ordered_at

        now = reference_now()
        hours_since_placed = (now - dt).total_seconds() / 3600
        # Check against 4 hour policy window
        return hours_since_placed <= 4

    except (ValueError, TypeError, AttributeError) as e:
        print(f"Warning: Could not parse cancellation window for order {getattr(order, 'order_id', 'unknown')}: {e}")
        return False

def evaluate_cancellation(state: WorkflowState) -> dict:
    policy = POLICIES.get("cancellation", {})
    order = state.get("order")
    
    if not order:
        decision = PolicyDecision(
            decision="needs_more_info",
            recommended_action="request_order_id",
            reason="Order id is required to process cancellation request",
            policy_summary=policy.get("summary", ""),
            policy_sources=[policy.get("policy_id", "cancellation_v1")],
            next_steps=["Ask user for order id"]
        ).model_dump()

    else:
            
        
        # Main business logic - use if / elif for clear priority
        if order.get("status") in ["shipped", "delivered"]:
            decision = PolicyDecision(
                decision="denied",
                recommended_action="explain_cannot_cancel_shipped_order",
                reason="Orders that have already shipped cannot be cancelled",
                policy_summary=policy.get("summary", ""),
                policy_sources=[policy.get("policy_id", "cancellation_v1")]
            ).model_dump()

        elif order.get("status") != "processing":
            decision = PolicyDecision(
                decision="denied",
                recommended_action="cannot_cancel_non_processing_order",
                reason="Only orders in processing status can be cancelled",
                policy_summary=policy.get("summary", ""),
                policy_sources=[policy.get("policy_id", "cancellation_v1")]
            ).model_dump()

        elif check_cancellation_window(order):
            decision = PolicyDecision(
                decision="approved",
                recommended_action="cancel_order",
                reason="Order is within 4-hour full cancellation window",
                policy_summary=policy.get("summary", ""),
                policy_sources=[policy.get("policy_id", "cancellation_v1")]
            ).model_dump()

        else:
            # Past 4 hours but still in processing → fee applies
            decision = PolicyDecision(
                decision="approved_with_fee",
                recommended_action="cancel_order_with_fee",
                reason="Order can be cancelled with 10 percent restocking fee",
                policy_summary=policy.get("summary", ""),
                policy_sources=[policy.get("policy_id", "cancellation_v1")]
            ).model_dump()

    return {
        "policy_decision": decision
    }

    
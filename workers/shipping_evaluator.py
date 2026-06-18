from schemas import PolicyDecision
from state.workflow_state import WorkflowState
from data.policy_store import POLICIES


def _shipping_reason(order: dict) -> str:
    """Internal audit string — facts for logs, LLM context, and templates."""
    parts = [
        f"order_id={order.get('order_id')}",
        f"status={order.get('status')}",
    ]
    carrier = order.get("carrier")
    if carrier:
        parts.append(f"carrier={carrier}")
    tracking = order.get("tracking_number")
    if tracking:
        parts.append(f"tracking={tracking}")
    eta = order.get("eta")
    if eta:
        parts.append(f"eta={eta}")
    delivered_at = order.get("delivered_at")
    if delivered_at:
        parts.append(f"delivered_at={delivered_at}")
    return "; ".join(parts)


def _shipping_action_and_decision(status: str) -> tuple[str, str]:
    """Map order status to recommended_action and decision bucket."""
    if status == "processing":
        return "explain_order_processing", "provide_shipping_status"
    if status == "shipped":
        return "explain_order_shipped", "provide_shipping_status"
    if status == "delivered":
        return "explain_order_delivered", "provide_shipping_status"
    if status == "returned":
        return "explain_order_returned", "provide_shipping_status"
    if status == "cancelled":
        return "explain_order_cancelled", "provide_shipping_status"
    return "explain_order_unknown_status", "provide_shipping_status"


def evaluate_shipping(state: WorkflowState) -> dict:
    policy = POLICIES.get(state.get("policy_domain"))
    order = state.get("order")

    if order is None:
        decision = PolicyDecision(
            decision="needs_more_info",
            recommended_action="request_order_id",
            reason="No order data available for shipping inquiry",
            policy_json=policy,
        ).model_dump()
    else:
        recommended_action, decision_value = _shipping_action_and_decision(
            order.get("status", "unknown")
        )
        decision = PolicyDecision(
            decision=decision_value,
            recommended_action=recommended_action,
            reason=_shipping_reason(order),
            policy_json=policy,
            policy_sources=[policy.get("policy_id")] if policy else [],
        ).model_dump()

    return {"policy_decision": decision}

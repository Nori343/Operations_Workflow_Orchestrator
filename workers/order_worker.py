from data.mock_orders import get_mock_order
from schemas import Order
from state.workflow_state import WorkflowState


def lookup_order(state: WorkflowState) -> dict:
    """Lookup order and attach it to state."""
    order_id = state.get("order_id")

    if not order_id:
        return {"order": None}

    raw = get_mock_order(order_id)
    if raw is None:
        return {"order": None}

    try:
        order = Order.model_validate(raw)
        return {"order": order.model_dump(mode="json")}
    except Exception as e:
        return {
            "order": None,
            "errors": [f"order: {e}"],
        }

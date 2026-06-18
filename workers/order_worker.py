from data.mock_orders import MOCK_ORDERS
from schemas import Order
from state.workflow_state import WorkflowState

def lookup_order(state: WorkflowState) -> dict:
    """Lookup order and attach it to state."""
    order_id = state.get("order_id")

    if not order_id:
        return {"order": None}

    if order_id not in MOCK_ORDERS:
        return {"order": None}

    try:
        order = Order.model_validate(MOCK_ORDERS[order_id])
        return {"order": order.model_dump(mode="json")}
    except Exception as e:
        return {
            "order": None,
            "errors": [f"order: {e}"],
        }
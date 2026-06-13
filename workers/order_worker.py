from data.mock_orders import MOCK_ORDERS
from schemas import Order
from state.workflow_state import WorkflowState

def lookup_order(state: WorkflowState) -> dict:
    """Lookup order and attach it to state"""
    order_id = state.get("order_id")                   # Extract once
    
    if order_id is not None and order_id in MOCK_ORDERS:
        order = Order(**MOCK_ORDERS[order_id])
        return {
            "order": order.model_dump(mode="json"),
        }
    else:
        return {
            "order": None
        }
    
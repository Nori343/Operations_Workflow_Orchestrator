from data.mock_orders import MOCK_ORDERS
from schemas import Order, WorkflowState

def lookup_order(state: WorkflowState) -> WorkflowState:
    """Lookup order and attach it to state"""
    order_id = state.order_id                    # Extract once
    
    if order_id is not None and order_id in MOCK_ORDERS:
        order = Order(**MOCK_ORDERS[order_id])
        state.order = order
    else:
        state.order = None                       # Be explicit
    
    return state
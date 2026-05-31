from data.policy_store import POLICIES
from schemas import PolicyDecision, WorkflowState
from datetime import datetime, timedelta
from workers.policy_handlers import policy_handler, returns_handler, shipping_handler, cancellation_handler

def check_return_window(state):
    order = state["order"]
    delivered_at = order["delivered_at"]
    dt = datetime.strptime(delivered_at, "%Y-%m-%d")
    return_deadline = dt + timedelta(days=30)
    now = datetime.now().date()
    is_within_return_window = now <= return_deadline.date()
    return is_within_return_window

def apply_policy(state: WorkflowState) -> WorkflowState:
    # Use dot notation consistently since it's now a Pydantic model
    workflow_type = state.workflow_type
    policy_domain = state.policy_domain   # ← Changed
    
    # === Policy Questions (General) ===
    if workflow_type and "policy" in workflow_type:
        return policy_handler(state)
    
    # === Request / Action Handlers ===
    elif workflow_type == "returns_request":
        return returns_handler(state)
    
    elif workflow_type == "shipping_request":
        return shipping_handler(state)        # Note: you had shipping_handler, not shipping_request_handler
    
    elif workflow_type == "cancellation_request":
        return cancellation_handler(state)
    
    # Fallback
    else:
        print(f"Warning: Unknown workflow_type '{workflow_type}', using policy_handler as fallback")
        return policy_handler(state)

    
if __name__ == "__main__":

    damaged_item_state = {
        "workflow_type": "damaged_items_request",
        "policy_domain": "damaged_items",
        "order": {
            "order_id": "XY-1234",
            "status": "delivered",
            "delivered_at": "2026-05-20 14:30",
        },
    }

    returns_state = {
        "workflow_type": "returns_request",
        "policy_domain": "returns",
        "order": {
            "order_id": "XY-5678",
            "status": "delivered",
            "delivered_at": "2026-05-10 14:30",
        },
    }

    print("\nDAMAGED ITEM TEST:")
    print(apply_policy(damaged_item_state))

    print("\nRETURNS TEST:")
    print(apply_policy(returns_state))
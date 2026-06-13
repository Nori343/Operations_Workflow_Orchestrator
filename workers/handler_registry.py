from workers.returns_evaluator import evaluate_returns
from workers.policy_evaluator import evaluate_policy
from workers.cancellation_evaluator import evaluate_cancellation
from workers.shipping_evaluator import evaluate_shipping
from workers.returns_evaluator import evaluate_returns
from workers.damaged_evaluator import evaluate_damaged
from workers.missing_package_evaluator import evaluate_missing_package

HANDLER_REGISTRY = {
    "returns_request": evaluate_returns,
    "shipping_request": evaluate_shipping,
    "cancellation_request": evaluate_cancellation,
    "damaged_items_request": evaluate_damaged,
    "missing_package_request": evaluate_missing_package,
    "returns_policy": evaluate_policy,
    "shipping_policy": evaluate_policy,
    "cancellation_policy": evaluate_policy,
    "damaged_items_policy": evaluate_policy,
    "missing_package_policy": evaluate_policy,
    "faqs_policy": evaluate_policy,
    "faqs_request": evaluate_policy
}

def get_handler(workflow_type:str|None):
    if not workflow_type:
        return evaluate_policy
    else:
        return HANDLER_REGISTRY.get(workflow_type, evaluate_policy)

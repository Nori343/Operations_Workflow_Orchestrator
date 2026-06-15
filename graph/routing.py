"""Conditional edge functions — declarative routing between nodes."""

from __future__ import annotations

from typing import Literal

from state.workflow_state import WorkflowState

AfterPlannerRoute = Literal["order", "policy"]


def route_after_planner(state: WorkflowState) -> AfterPlannerRoute:
    """
    Skip order lookup when order context is not needed.

    Action requests without an order_id go straight to policy, which returns
    needs_more_info / request_order_id.
    """
    requires_order = state.get("requires_order", False)
    has_order_id = bool(state.get("order_id"))

    if requires_order and has_order_id:
        return "order"
    return "policy"

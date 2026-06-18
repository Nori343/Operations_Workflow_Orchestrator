from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from graph.routing import route_after_planner
from nodes.order import order_node
from nodes.planner import planner_node
from nodes.policy import policy_node
from nodes.response import response_node
from nodes.risk import risk_node
from schemas import SupportTicket
from state.workflow_state import WorkflowState

# ====================== BUILD GRAPH ======================
def graph_builder(*, enable_checkpointing: bool = True):
    graph = StateGraph(WorkflowState)

    graph.add_node("planner", planner_node)
    graph.add_node("order", order_node)
    graph.add_node("policy", policy_node)
    graph.add_node("risk", risk_node)
    graph.add_node("response", response_node)

    graph.add_edge(START, "planner")
    graph.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "order": "order",
            "policy": "policy"
        }
    )
    graph.add_edge("order", "policy")
    graph.add_edge("policy", "risk")
    graph.add_edge("risk", "response")
    graph.add_edge("response", END)

    checkpointer = MemorySaver() if enable_checkpointing else None
    return graph.compile(checkpointer=checkpointer)

workflow_app = graph_builder(enable_checkpointing=True) 


# ====================== TEST ======================
if __name__ == "__main__":
    ticket = SupportTicket(
        ticket_id="1",
        customer_message="My order is XY-1002, Can I return it?"
    )
    
    result = workflow_app.invoke(ticket.model_dump())
    print(result)
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

from planner import classify_workflow
from workers.order_worker import lookup_order
from workers.policy_worker import apply_policy
from workers.risk_worker import measure_risk
from workers.response_worker import craft_response
from schemas import PolicyDecision, SupportTicket, Order, WorkflowState
from typing import Optional
from pydantic import Field, BaseModel



def planner_node(state: WorkflowState):
    return classify_workflow(state.customer_message)


def order_node(state: WorkflowState):
    return lookup_order(state)


def policy_node(state: WorkflowState):
    return apply_policy(state)


def response_node(state: WorkflowState):
    return craft_response(state)



# ====================== BUILD GRAPH ======================

graph = StateGraph(WorkflowState)

graph.add_node("planner", planner_node)
graph.add_node("order", order_node)
graph.add_node("policy", policy_node)
graph.add_node("response", response_node)

# Updated edges - skipping risk for now
graph.add_edge(START, "planner")
graph.add_edge("planner", "order")
graph.add_edge("order", "policy")
graph.add_edge("policy", "response")   # ← direct to response
graph.add_edge("response", END)

workflow_app = graph.compile()


# ====================== TEST ======================
if __name__ == "__main__":
    ticket = SupportTicket(
        ticket_id="1",
        customer_message="My order is XY-1002, Can I return it?"
    )
    
    result = workflow_app.invoke(ticket.model_dump())
    print(result)
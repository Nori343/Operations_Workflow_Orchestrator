from dotenv import load_dotenv
from fastapi import FastAPI
from langchain_core.messages import HumanMessage

from schemas import SupportTicket
from graph.builder import workflow_app

load_dotenv()

app = FastAPI()


def to_ticket_response(ticket: SupportTicket, result: dict, *, debug: bool = False) -> dict:
    risk = result.get("risk_decision") or {}
    payload = {
        "conversation_id": ticket.conversation_id,
        "response": result.get("response") or "",
        "missing_fields": result.get("missing_fields") or [],
        "order_id": result.get("order_id"),
        "escalation_required": bool(risk.get("escalation_required")),
        "workflow_type": result.get("workflow_type"),
        "planner_source": result.get("planner_source"),
    }
    if debug:
        payload["debug"] = {
            "policy_decision": result.get("policy_decision"),
            "risk_decision": risk,
            "node_trace": result.get("node_trace"),
            "errors": result.get("errors"),
        }
    return payload

@app.post("/process-ticket")
def process_ticket(ticket: SupportTicket):
    turn_input = {
    **ticket.model_dump(),
    "messages": [HumanMessage(content=ticket.customer_message)]
    }
   
    config = {"configurable": {"thread_id": f"conversation_id-{ticket.conversation_id}"}}
    result = workflow_app.invoke(turn_input, config=config)
    return to_ticket_response(ticket, result)
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from langchain_core.messages import HumanMessage
from pydantic import ValidationError

from graph.builder import workflow_app
from schemas import SupportTicket, TicketDebugInfo, TicketResponse

load_dotenv()

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def to_ticket_response(
    ticket: SupportTicket, result: dict, *, debug: bool = False
) -> TicketResponse:
    risk = result.get("risk_decision") or {}
    payload: dict = {
        "conversation_id": ticket.conversation_id,
        "response": result.get("response") or "",
        "missing_fields": result.get("missing_fields") or [],
        "order_id": result.get("order_id"),
        "escalation_required": bool(risk.get("escalation_required")),
        "workflow_type": result.get("workflow_type"),
        "planner_source": result.get("planner_source"),
    }
    if debug:
        payload["debug"] = TicketDebugInfo(
            policy_decision=result.get("policy_decision"),
            risk_decision=risk or None,
            node_trace=result.get("node_trace") or [],
            errors=result.get("errors") or [],
        )
    return TicketResponse.model_validate(payload)


@app.post("/process-ticket", response_model=TicketResponse)
def process_ticket(
    ticket: SupportTicket,
    debug: bool = Query(False, description="Include policy, risk, trace, and errors in response"),
) -> TicketResponse:
    turn_input = {
        **ticket.model_dump(),
        "messages": [HumanMessage(content=ticket.customer_message)],
    }
    config = {"configurable": {"thread_id": f"conversation_id-{ticket.conversation_id}"}}

    try:
        result = workflow_app.invoke(turn_input, config=config)
        return to_ticket_response(ticket, result, debug=debug)
    except ValidationError as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": "invalid_graph_output", "validation": exc.errors()},
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": "workflow_failed", "message": str(exc)},
        ) from exc

from dotenv import load_dotenv
from fastapi import FastAPI

from schemas import SupportTicket
from graph.builder import workflow_app

load_dotenv()

app = FastAPI()


@app.post("/process-ticket")
def process_ticket(ticket: SupportTicket):
    config = {"configurable": {"thread_id": f"ticket-{ticket.ticket_id}"}}
    return workflow_app.invoke(ticket.model_dump(), config=config)
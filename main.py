from dotenv import load_dotenv
from fastapi import FastAPI

from schemas import SupportTicket
from workflow_graph import workflow_app

load_dotenv()

app = FastAPI()


@app.post("/process-ticket")
def process_ticket(ticket: SupportTicket):
    return workflow_app.invoke(ticket.model_dump())
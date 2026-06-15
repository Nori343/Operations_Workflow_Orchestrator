from __future__ import annotations

import operator
from typing import Annotated, Any

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

class WorkflowState(TypedDict, total=False):
    ticket_id: str
    customer_message: str
    # Planner
    planner_source: str | None
    order_id: str | None
    intent: str | None
    policy_domain: str | None      
    workflow_type: str | None
    requires_order: bool
    missing_fields: list[str]
    top_score: int
    ambiguous: bool
    matched_terms: list[str]
    candidate_domains: list[str]
    confidence: float
    intent_confidence: float
    tiebreak_applied: bool
    # External stubs 
    has_damage_photo: bool
    photo_review_status: str | None
    carrier_investigation_status: str | None
    # Workers 
    order: dict[str, Any] | None
    policy_decision: dict[str, Any] | None
    risk_decision: dict[str, Any] | None   
    response: str | None                  
    # Observability
    messages: Annotated[list[BaseMessage], add_messages]
    node_trace: Annotated[list[str], operator.add]
    errors: Annotated[list[str], operator.add]

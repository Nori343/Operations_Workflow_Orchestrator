from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime




class SupportTicket(BaseModel):
    conversation_id: str
    customer_message: str

class Order(BaseModel):
    order_id: str
    customer_id: Optional[str] = None
    
    status: str                    # processing, shipped, delivered, returned, cancelled
    total: float
    items: list[str]
    
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    
    # Timestamps
    ordered_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None
    eta: Optional[datetime] = None
    
    # Useful for realism
    contains_clearance_items: bool = False
    contains_custom_items: bool = False
    is_premium_member: bool = False
    shipping_address_zip: Optional[str] = None
    is_international: bool = False


class PlannerOutput(BaseModel):
    """Structured output from the planner/classifier stage."""

    order_id: str | None = None
    policy_domain: str
    intent: Literal["action", "policy"]
    workflow_type: str
    requires_order: bool = False
    missing_fields: list[str] = Field(default_factory=list)
    intent_confidence: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    planner_source: str = "heuristic"
    top_score: int = 0
    second_score: int = 0
    candidate_domains: list[str] = Field(default_factory=list)
    ambiguous: bool = False
    matched_terms: list[str] = Field(default_factory=list)
    tiebreak_applied: bool = False


class PolicyDecision(BaseModel):
    decision: str                    # "approved", "denied", "needs_more_info", "escalate", etc.
    recommended_action: str          # "start_return_process", "explain_policy", "request_photo", etc.
    reason: str                      # Short, clear explanation
    policy_summary: Optional[str] = None              # For Response Worker to use
    policy_sources: Optional[list[str]] = None       # e.g. ["returns_v1", "damaged_v1"]
    policy_json: Optional[dict] = None
    next_steps: list[str] = Field(default_factory=list)      # e.g. ["upload_photo", "wait_for_investigation"]

class RiskDecision(BaseModel):
    escalation_required: bool
    recommended_action: str
    risk_level: str
    reason: str
    risk_flags: list[str] = Field(default_factory=list)


class TicketDebugInfo(BaseModel):
    policy_decision: dict | None = None
    risk_decision: dict | None = None
    node_trace: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class TicketResponse(BaseModel):
    conversation_id: str
    response: str
    missing_fields: list[str] = Field(default_factory=list)
    order_id: str | None = None
    escalation_required: bool = False
    workflow_type: str | None = None
    planner_source: str | None = None
    debug: TicketDebugInfo | None = None


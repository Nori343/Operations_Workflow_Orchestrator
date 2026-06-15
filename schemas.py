from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime




class SupportTicket(BaseModel):
    ticket_id: str
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
    risk_level: str
    reason: str
    risk_flags: list[str] = Field(default_factory=list) 
   # recommended_action: str




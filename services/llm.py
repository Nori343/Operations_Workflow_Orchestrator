from __future__ import annotations

import json

from openai import OpenAI

from config.settings import settings
from services.template_response import template_response
from state.workflow_state import WorkflowState
from langchain_core.messages import AIMessage

_client: OpenAI | None = None

def _get_client()->OpenAI | None:
    global _client
    if not settings.llm.is_available:
        return None 
    if _client is None:
        _client = OpenAI(
            api_key=settings.llm.api_key,
            timeout=settings.llm.timeout_seconds,
            max_retries=settings.llm.max_retries
        )
    return _client

def build_response_context(state: WorkflowState) -> dict:
    history = [
        {"role": m.type, "content": str(m.content)}
        for m in state.get("messages") or []
        if not str(m.content).startswith("[")  # skip [planner] traces
    ]

    intent = state.get("intent")
    is_policy_turn = intent == "policy" or (state.get("workflow_type") or "").endswith("_policy")
    return {
        "customer_message": state.get("customer_message"),
        "order": None if is_policy_turn else state.get("order"),
        "policy_decision": state.get("policy_decision"),
        "risk_decision": state.get("risk_decision"),
        "conversation_history":history
    }


def craft_response(state: WorkflowState) -> dict:
    context = build_response_context(state)
    client = _get_client()
    if client is None:
        return template_response(context)
    summary = json.dumps(context, default=str, indent=2)
    system_prompt = """
You are a customer response synthesizer.

Your job is to convert structured operational summary into a clear customer-facing response.

Rules:
- Use policy_decision.recommended_action and reason as authoritative operational guidance.
- Follow policy_decision.recommended_action.
- Use the order, customer_message, and conversation_history only for relevant context.
- Do not change or override the policy decision.
- Explain eligibility and next steps only. This system does not execute returns, cancellations, refunds, or investigations.
- Do not claim any action has already been completed (no emails sent, labels issued, orders cancelled, or investigations opened).
- Do not ask the customer to reply YES/NO to confirm an action this system will perform.
- Only use risk_decision to alter the response if risk_decision.escalation_required is True. If so, state that the case requires review by support and use risk_decision.reason as the explanation.
- Do not promise a refund unless explicitly allowed by the policy decision.
- Do not invent policy details, timelines, discounts, credits, or escalation steps.
- If more information is needed, clearly ask for the missing information.
- Keep the response concise and under 80 words.
- Avoid generic closing phrases unless they add necessary information.
- End the response after communicating the required operational next step.
"""
    try:
        response = client.chat.completions.create(
            model=settings.llm.model,
            messages=[{
                "role": "system",
                "content":system_prompt
            },
            {
                "role":"user",
                "content": f"""summary:{summary}
                """
            }],
            temperature=0.2,
            )
        answer = (response.choices[0].message.content or "").strip()
        return {
            "response": answer,
            "messages": [AIMessage(content=answer)]
        }
    except Exception as e:
        return {**template_response(context), "errors": [f"craft_response: {e}"]}
        
VALID_DOMAINS = {
    "returns",
    "shipping",
    "cancellation",
    "damaged_items",
    "missing_package",
    "faqs",
    "unsupported",
}
VALID_INTENTS = {"action", "policy"}

def classify_with_llm(message: str, *, domain: str, intent: str, candidates: list[str]) -> dict[str, str] | None:
    client = _get_client()
    if client is None:
        return None
    allowed = candidates or sorted(VALID_DOMAINS - {"unsupported"})
    context = json.dumps(
        {
            "customer_message": message,
            "heuristic_guess": {
                "policy_domain": domain,
                "intent": intent,
                "candidate_domains": allowed,
            },
        },
        indent=2,
    )
    system_prompt = f"""You classify customer support tickets for PeakGear Fitness.
    You take in context from a heuristic based planner and which domain and intent it picked,
    its confidence in that pick, the possible candidates it believes are relevant, the matched 
    terms it used to order the domains, and the orignal customer message.

Return JSON only:
{{"policy_domain": "<domain>", "intent": "action" or "policy"}}
INTENT:
- "action" = customer wants something done on a specific order (return, cancel, track, report damage, missing package).
- "policy" = general question about rules/process, no specific order action required.
DOMAINS (pick exactly one):
- returns: returns, refunds, exchanges, send item back
- shipping: tracking, delivery status, ETA, where is my order
- cancellation: cancel or stop an order before/at ship
- damaged_items: item arrived broken, defective, damaged
- missing_package: delivered but not received, stolen, never arrived
- faqs: company info (founders, mission, location) — always intent "policy"
- unsupported: not related to PeakGear orders/support 
policy_domain MUST be one of: {allowed}
If nothing fits, return "unsupported" for "policy_domain" and "policy" for "intent'.
Use the heuristic_guess as a hint, not gospel — override if the message clearly fits another allowed domain.
"""

    try:
        response = client.chat.completions.create(
            model=settings.llm.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context},
            ],
            temperature=0,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "planner_classification",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "policy_domain": {"type": "string", "enum": ["returns", "shipping", "cancellation", "damaged_items", "missing_package", "faqs", "unsupported"]},
                            "intent": {"type": "string", "enum": ["action", "policy"]},
                        },
                        "required": ["policy_domain", "intent"],
                        "additionalProperties": False,
                    },
                },
            }
        )
        content = response.choices[0].message.content or "{}"
        answer = json.loads(content)
    except Exception:
        return None
    domain = answer.get("policy_domain")
    if domain != "unsupported" and domain not in allowed:
        return None
    if domain in ("faqs", "unsupported"):
        intent = "policy"
    return {
        "policy_domain": domain,
        "intent": intent,
    }
    
    

from dotenv import load_dotenv
from openai import OpenAI
import os
from schemas import WorkflowState

load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=30.0,
    max_retries=1,
)

def build_response_context(state: WorkflowState) -> dict:
    return {
        "customer_message": state.customer_message,
        "order": state.order,
        "policy_decision": state.policy_decision,
        "risk_decision": state.risk_decision
    }

def craft_response(state:WorkflowState):
    summary = build_response_context(state)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "system",
            "content":"""
You are a customer response synthesizer.

Your job is to convert structured operational summary into a clear customer-facing response.

Rules:
- Use policy_decision.recommended_action and reason as authoritative operational guidance.
- Follow policy_decision.recommended_action.
- Use the order and customer_message only for relevant context.
- Do not change or override the policy decision.
- Only use risk_decision to alter the response if risk_decision.escalation_required is True. If so, mention that the case will be reviewed by support and use risk_decision.reason as the explanation.
- Do not promise a refund unless explicitly allowed by the policy decision.
- Do not claim any action has already been completed.
- Do not invent policy details, timelines, discounts, credits, or escalation steps.
- If more information is needed, clearly ask for the missing information.
- If human review is required, explain that the case will be reviewed by support.
- Keep the response concise and under 80 words.
- Avoid generic closing phrases unless they add necessary information.
- End the response after communicating the required operational next step.
"""
        },
        {
            "role":"user",
            "content": f"""summary:{summary}
            """
        }])
    answer = response.choices[0].message.content
    return {
        "response": answer
    }
    

if __name__ == "__main__":
    test_state = {
        "customer_message": "My item arrived damaged. Can I get a refund?",
        "workflow_type": "damaged_items_request",
        "order": {
            "order_id": "XY-1234",
            "status": "delivered",
            "delivered_at": "2026-05-20 14:30",
            "total": 79.99,
        },
        "policy_decision": {
            "decision": "needs_more_info",
            "recommended_action": "request_damage_photo",
            "reason": "A damage photo is required before approving a replacement or refund.",
        },
        "risk_decision": {
            "escalation_required": False,
            "risk_level": "low",
            "reason": "No escalation rule triggered.",
            "risk_flags": ["damaged_items_claim"],
        },
    }

    result = craft_response(test_state)
    print(result)
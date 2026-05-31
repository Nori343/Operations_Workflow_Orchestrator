import re

ACTION_SIGNALS = [
    "can i",
    "i want to",
    "help me",
    "my order",
    "need to",
    "my package",
    "check"
]

POLICY_SIGNALS = [
    "what is your",
    "how does",
    "do you allow",
    "policy",
    "how long",
    "what is",
    "can you",
    "what's",
    "whats",
    "do you"
]

DOMAIN_SIGNALS = {
    "returns": [
        "return",
        "refund",
        "money back",
        "return window",
        "send back",
    ],
    "shipping": [
        "shipping",
        "delivery",
        "tracking",
        "eta",
        "where is",
        "ship",
        "when"
    ],
    "cancellation": [
        "cancel",
        "stop my order",
    ],
    "damaged_items": [
        "damaged",
        "broken",
        "cracked",
        "defective",
    ],
    "missing_package": [
        "missing",
        "never arrived",
        "says delivered",
        "not delivered",
        "not at my door",
        "missing package",
        "never got",
        "never received",
        "didn't receive",
        "did not receive",
        "didn't get",
        "did not get",
        "says delivered",
        "marked delivered",
        "delivered but i never got it",
        "delivered but not received",
    ],
}

def extract_order_id(message: str) -> str | None:
    """Normalize explicit order IDs like XY-2048 or bare IDs like 2048."""
    message = message.upper()

    m = re.search(r'\bPG-(\d{4})\b', message)
    if m:
        return f"PG-{m.group(1)}"

    m = re.search(r'\b(\d{4})\b', message)
    if m:
        return f"PG-{m.group(1)}"
    return None

def phrase_matches(message: str, phrase: str) -> bool:
    if " " in phrase:
        return phrase in message

    return re.search(rf"\b{re.escape(phrase)}\b", message) is not None

def detect_policy_domain(message: str) -> dict:
    message = message.lower()
    scores = {}

    for domain, words in DOMAIN_SIGNALS.items():
        score = 0
        matched_terms = []

        for word in words:
            if phrase_matches(message, word):
                score += 1
                matched_terms.append(word)

            scores[domain] = {
                "score": score,
                "matched_terms": matched_terms,
            }

    highest_score = max(data["score"] for data in scores.values())

    if highest_score == 0:
        return {
            "policy_domain": "unsupported",
            "top_score": 0,
            "candidate_domains": [],
            "ambiguous": False,
            "matched_terms": [],
        }

    top_domains = [
        domain
        for domain, data in scores.items()
        if data["score"] == highest_score
    ]

    best_domain = top_domains[0]

    return {
        "policy_domain": best_domain,
        "top_score": highest_score,
        "candidate_domains": top_domains,
        "ambiguous": len(top_domains) > 1,
        "matched_terms": scores[best_domain]["matched_terms"],
    }

def detect_intent(text: str) -> str:
    action_score = 0
    policy_score = 0
    text = text.lower()

    for signal in ACTION_SIGNALS:
        if signal in text:
            action_score += 1

    for signal in POLICY_SIGNALS:
        if signal in text:
            policy_score += 1

    if action_score >= policy_score:
        return "action"

    return "policy"

def build_workflow_type(policy_domain: str, intent: str) -> str:
    if policy_domain == "unknown":
        return "unsupported"

    if intent == "policy":
        return f"{policy_domain}_policy"

    return f"{policy_domain}_request"

def classify_workflow(message: str) -> dict:
    message = message.lower()
    order_id = extract_order_id(message)
    domain_result = detect_policy_domain(message)
    intent = detect_intent(message)
    workflow_type = build_workflow_type(domain_result["policy_domain"], intent)
    return {
        "order_id":order_id,
        "intent":intent,
        "workflow_type":workflow_type,
        "requires_order": intent == "action",
        "missing_fields": ["order_id"] if intent == "action" and not order_id else [],
        **domain_result
    }
    
if __name__ == "__main__":
    test_messages = [
        "What is your return policy?",
        "Can I return order XY-1234?",
        "My package says delivered but it is not at my door. XY-1234",
        "My item arrived broken. Order XY-1234",
        "Where is my order XY-1234?",
        "What is your shipping policy?",
        "Can I cancel order XY-1234?",
        "I want a refund for XY-1234",
        "My package never arrived",
        "Do you ship internationally?",
        "My order is 1234, what is your return and shipping policy?"
    ]

    for message in test_messages:
        print("\nMESSAGE:", message)
        print(classify_workflow(message))
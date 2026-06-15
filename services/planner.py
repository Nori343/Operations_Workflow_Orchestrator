"""Planner service — keyword classification and workflow routing inputs."""

from __future__ import annotations

import re

from config.settings import settings
from services.llm import classify_with_llm

ACTION_SIGNALS = [
    "can i",
    "i want to",
    "help me",
    "my order",
    "need to",
    "my package",
    "check",
    "when will",
    "how long until",
    "where is my",
    "track my",
]

POLICY_SIGNALS = [
    "what is your",
    "how does",
    "do you allow",
    "policy",
    "how long does",
    "what is",
    "can you",
    "what's",
    "whats",
    "do you",
    "what happens",
    "if",
    "when was",
    "tell me about",
]

DOMAIN_SIGNALS = {
    "returns": [
        "return",
        "refund",
        "money back",
        "return window",
        "send back",
        "exchange",
        "wrong size",
        "doesn't fit",
        "does not fit",
        "return label",
    ],
    "shipping": [
        "shipping",
        "delivery",
        "tracking",
        "eta",
        "where is",
        "ship",
        "when will",
        "in transit",
        "out for delivery",
        "international",
        "tracking number",
        "shipment status",
    ],
    "cancellation": [
        "cancel",
        "cancellation",
        "stop my order",
        "stop shipment",
        "stop order",
        "hold order",
        "don't ship",
        "do not ship",
        "halt order",
        "cancel order",
    ],
    "damaged_items": [
        "damaged",
        "broken",
        "cracked",
        "defective",
        "damage",
        "crushed",
        "torn",
        "leaked",
        "smashed",
        "arrived broken",
    ],
    "missing_package": [
        "missing",
        "never arrived",
        "never came",
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
        "marked delivered",
        "delivered but i never got it",
        "delivered but not received",
        "still waiting",
        "hasn't shown up",
        "has not shown up",
        "lost package",
        "stolen",
        "porch pirate",
    ],
    "faqs": [
        "founded",
        "founders",
        "mission",
        "headquarters",
        "company located",
        "based out of",
        "who are you",
        "about your company",
        "where are you located",
        "company history",
    ],
}

# When keyword scores tie, pick the highest-priority domain among candidates.
DOMAIN_PRIORITY = [
    "cancellation",
    "missing_package",
    "damaged_items",
    "returns",
    "shipping",
    "faqs",
]


def extract_order_id(message: str) -> str | None:
    """Normalize explicit order IDs like PG-2048 or bare IDs like 2048."""
    message = message.upper()

    m = re.search(r"\bPG-(\d{4})\b", message)
    if m:
        return f"PG-{m.group(1)}"

    m = re.search(r"\b(\d{4})\b", message)
    if m:
        return f"PG-{m.group(1)}"
    return None


def phrase_matches(message: str, phrase: str) -> bool:
    if " " in phrase:
        return phrase in message

    return re.search(rf"\b{re.escape(phrase)}\b", message) is not None


def score_domains(message: str) -> dict[str, dict]:
    """Return per-domain hit counts and matched terms."""
    scores: dict[str, dict] = {}

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

    return scores


def compute_confidence(top: int, second: int, tied_at_top: bool) -> float:
    """Bucket heuristic confidence. Gate LLM when score is below threshold (default 0.67)."""
    if top == 0:
        return 0.0
    if tied_at_top:
        return 0.0
    if second == 0:
        return 0.67 if top == 1 else 1.0
    if top - second == 1:
        return 0.33
    return 0.67


def compute_intent_confidence(action_score: int, policy_score: int) -> float:
    total = action_score + policy_score
    if total == 0:
        return 0.5
    return round(abs(action_score - policy_score) / total, 2)


def resolve_tied_domains(candidates: list[str]) -> tuple[str, bool]:
    """Pick one domain when keyword scores tie (highest priority wins)."""
    if len(candidates) == 1:
        return candidates[0], False

    for domain in DOMAIN_PRIORITY:
        if domain in candidates:
            return domain, True

    return candidates[0], False


def detect_policy_domain(message: str) -> dict:
    message = message.lower()
    domain_scores = score_domains(message)
    scores = {domain: data["score"] for domain, data in domain_scores.items()}
    highest_score = max(scores.values())

    if highest_score == 0:
        return {
            "policy_domain": "unsupported",
            "top_score": 0,
            "second_score": 0,
            "candidate_domains": [],
            "ambiguous": False,
            "matched_terms": [],
            "confidence": 0.0,
            "tiebreak_applied": False,
        }

    sorted_scores = sorted(scores.values(), reverse=True)
    second_score = sorted_scores[1]
    top_domains = [domain for domain, score in scores.items() if score == highest_score]
    tied_at_top = len(top_domains) > 1
    ambiguous = tied_at_top
    best_domain, tiebreak_applied = resolve_tied_domains(top_domains)

    return {
        "policy_domain": best_domain,
        "top_score": highest_score,
        "second_score": second_score,
        "candidate_domains": top_domains,
        "ambiguous": ambiguous and not tiebreak_applied,
        "matched_terms": domain_scores[best_domain]["matched_terms"],
        "confidence": compute_confidence(highest_score, second_score, tied_at_top),
        "tiebreak_applied": tiebreak_applied,
    }


def detect_intent(text: str) -> tuple[str, float]:
    action_score = 0
    policy_score = 0
    text = text.lower()

    for signal in ACTION_SIGNALS:
        if signal in text:
            action_score += 1

    for signal in POLICY_SIGNALS:
        if signal in text:
            policy_score += 1

    intent = "action" if action_score >= policy_score else "policy"
    return intent, compute_intent_confidence(action_score, policy_score)


def build_workflow_type(policy_domain: str, intent: str) -> str:
    if policy_domain == "unsupported":
        return "unsupported"
    if policy_domain == "faqs":
        return f"{policy_domain}_policy"
    if intent == "policy":
        return f"{policy_domain}_policy"

    return f"{policy_domain}_request"


def explain_classification(message: str) -> dict:
    result = classify_workflow(message)
    threshold = settings.planner_confidence_threshold
    print(f"message: {message}")
    print(f"domain: {result['policy_domain']}  intent: {result['intent']}")
    print(f"scores: top={result['top_score']} second={result['second_score']}")
    print(
        f"confidence: {result['confidence']}  "
        f"threshold: {threshold}  source: {result['planner_source']}"
    )
    print(f"terms: {result['matched_terms']}  tiebreak: {result['tiebreak_applied']}")
    return result


def classify_workflow(message: str) -> dict:
    normalized = message.lower()
    order_id = extract_order_id(message)
    domain_meta = detect_policy_domain(normalized)
    intent, intent_confidence = detect_intent(normalized)

    domain = domain_meta["policy_domain"]
    threshold = settings.planner_confidence_threshold
    confidence = domain_meta["confidence"]
    if domain_meta["tiebreak_applied"]:
        confidence = max(confidence, threshold)

    source = "heuristic"
    if confidence < threshold:
        llm_pick = classify_with_llm(
            message,
            domain=domain,
            intent=intent,
            candidates=domain_meta["candidate_domains"],
        )
        if llm_pick:
            domain = llm_pick["policy_domain"]
            intent = llm_pick["intent"]
            source = "llm"

    return {
        "order_id": order_id,
        "policy_domain": domain,
        "intent": intent,
        "workflow_type": build_workflow_type(domain, intent),
        "requires_order": intent == "action",
        "missing_fields": ["order_id"] if intent == "action" and not order_id else [],
        "intent_confidence": intent_confidence,
        "confidence": confidence,
        "planner_source": source,
        "top_score": domain_meta["top_score"],
        "second_score": domain_meta["second_score"],
        "candidate_domains": domain_meta["candidate_domains"],
        "ambiguous": False if source == "llm" else domain_meta["ambiguous"],
        "matched_terms": domain_meta["matched_terms"],
        "tiebreak_applied": domain_meta["tiebreak_applied"],
    }




if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--trace":
        messages = sys.argv[2:] or ["How do I cancel and get a refund?"]
        for message in messages:
            explain_classification(message)
            print()
    else:
        print("Usage: python -m services.planner --trace \"your message here\"")
        print("Example messages:")
        for message in [
            "Can I return order PG-1001?",
            "How do I cancel and get a refund?",
            "My order never came but tracking says delivered",
        ]:
            print(f"  python -m services.planner --trace \"{message}\"")

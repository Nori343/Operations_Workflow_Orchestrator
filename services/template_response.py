"""Deterministic customer-facing templates keyed on PolicyDecision.recommended_action."""

from __future__ import annotations

from typing import Any


def build_template_response(context: dict[str, Any]) -> str:
    """
    Map recommended_action → canned customer copy.

    Keys match PolicyDecision.recommended_action values from policy workers.
    Unknown actions fall back to policy summary or reason.
    """
    policy = context.get("policy_decision") or {}
    risk = context.get("risk_decision") or {}
    order = context.get("order") or {}
    oid = order.get("order_id") or ""
    action = policy.get("recommended_action", "generate_response")
    reason = policy.get("reason", "")

    shipped_msg = f"Order {oid} has shipped"
    carrier = order.get("carrier")
    if carrier:
        shipped_msg += f" via {carrier}"
    shipped_msg += "."
    tracking = order.get("tracking_number")
    if tracking:
        shipped_msg += f" Tracking: {tracking}."
    eta = order.get("eta")
    if eta:
        shipped_msg += f" Estimated delivery: {eta}."

    processing_msg = f"Order {oid} is processing and should ship within 1-2 business days."
    if eta:
        processing_msg += f" Estimated delivery: {eta}."

    delivered_at = order.get("delivered_at")
    delivered_suffix = f" on {delivered_at}." if delivered_at else "."
    delivered_msg = f"Order {oid} was delivered{delivered_suffix}"

    templates: dict[str, str] = {
        # Shipping
        "explain_order_processing": processing_msg,
        "explain_order_shipped": shipped_msg,
        "explain_order_delivered": delivered_msg,
        "explain_order_returned": (
            f"Order {oid} has been returned. Contact support if you have questions about this order."
        ),
        "explain_order_cancelled": (
            f"Order {oid} was cancelled."
        ),
        "explain_order_unknown_status": (
            f"Order {oid} has status {order.get('status', 'unknown')}. Contact support for details."
        ),
        # Returns
        "explain_return_approved": (
            f"Order {oid} is eligible for return under our policy. "
            "Next step: contact support with this order number for return instructions."
        ),
        "explain_non_returnable_status": (
            f"Order {oid} cannot be returned in its current status. "
            f"{reason}"
        ).strip(),
        "explain_non_eligible_items": (
            f"Order {oid} contains clearance or custom items that are not eligible for return."
        ),
        "explain_past_return_window": (
            f"Order {oid} is outside the return window. {reason}"
        ).strip(),
        # Cancellation
        "cancel_order": (
            f"Order {oid} is within the free cancellation window and may be cancelled for a full refund. "
            "Contact support to complete the cancellation."
        ),
        "cancel_order_with_fee": (
            f"Order {oid} may be cancelled with a 10% restocking fee. "
            "Contact support to proceed."
        ),
        "explain_cannot_cancel_shipped_order": (
            f"Order {oid} has already shipped and cannot be cancelled. "
            "You may request a return after delivery if eligible."
        ),
        "cannot_cancel_non_processing_order": (
            f"Order {oid} cannot be cancelled because only processing orders are eligible. "
            f"{reason}"
        ).strip(),
        # Damaged items
        "explain_non_eligible_status": (
            f"Order {oid} is not eligible for a damage claim in its current status. "
            f"{reason}"
        ).strip(),
        "explain_outside_damaged_report_window": (
            f"Order {oid} is outside the 7-day damaged-item report window. "
            f"{reason}"
        ).strip(),
        "request_photo_of_damged_item": (
            f"To evaluate your damage claim for order {oid}, please provide clear photos "
            "of the item and packaging."
        ),
        "explain_phoot_review_denied": (
            f"We could not verify the damage photos for order {oid}. "
            "Please contact support if you believe this is an error."
        ),
        "explain_photo_under_review": (
            f"Your damage photos for order {oid} are under review by support."
        ),
        "explain_damged_item_return_approved": (
            f"Your damage claim for order {oid} is approved under our policy. "
            "Contact support for return or replacement next steps."
        ),
        # Missing package
        "pending_customer_wait": (
            f"For order {oid}, wait 2 business days after the delivered scan "
            "and check with neighbors or building staff before contacting support "
            "about a missing package."
        ),
        "carrier_investigation_open": (
            f"Order {oid} qualifies for a carrier investigation, which typically takes 3-5 business days. "
            "Support will handle the investigation."
        ),
        "explain_carrier_investigation_underway": (
            f"A carrier investigation is already in progress for order {oid}. "
            "Contact support for status updates."
        ),
        "explain_carrier_investigation_found_contradictory_evidence": (
            f"Our carrier investigation for order {oid} found delivery was completed. "
            "Contact support if you still believe the package is missing."
        ),
        "explain_return/replacement_approved": (
            f"Your missing-package claim for order {oid} is approved under our policy. "
            "Contact support to arrange a refund or replacement."
        ),
        # Shared
        "request_order_id": (
            "To help with your request, please provide your order number (format PG-XXXX)."
        ),
    }

    policy_json = policy.get("policy_json") or {}
    summary = policy.get("policy_summary") or policy_json.get("summary")
    if summary:
        fallback = summary
    elif reason:
        fallback = reason
    else:
        fallback = "Thank you for contacting PeakGear Fitness support."

    if action == "generate_response":
        base = fallback
    else:
        base = templates.get(action, fallback)

    if risk.get("escalation_required"):
        base += f" This case requires review by a support specialist: {risk.get('reason', '')}"

    return base.strip()


def template_response(context: dict[str, Any]) -> dict[str, str]:
    return {"response": build_template_response(context)}

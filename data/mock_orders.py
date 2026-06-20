"""Mock order catalog — dates resolved relative to config.clock.reference_now()."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from config.clock import reference_now

# Offset keys are stripped before return; they define scenario timing, not fixed calendar dates.
_MOCK_ORDER_TEMPLATES: dict[str, dict[str, Any]] = {
    "PG-1001": {
        "order_id": "PG-1001",
        "customer_id": "cust_001",
        "status": "delivered",
        "total": 189.98,
        "items": ["Adjustable Dumbbells (Pair)", "Foam Roller"],
        "carrier": "UPS",
        "tracking_number": "1Z9999999999999999",
        "ordered_days_ago": 15,
        "shipped_days_ago": 14,
        "delivered_days_ago": 10,
        "shipping_address_zip": "92008",
        "is_international": False,
        "is_premium_member": True,
        "contains_clearance_items": False,
        "contains_custom_items": False,
    },
    "PG-1002": {
        "order_id": "PG-1002",
        "customer_id": "cust_002",
        "status": "shipped",
        "total": 89.98,
        "items": ["Resistance Bands Set", "32oz Insulated Water Bottle"],
        "carrier": "FedEx",
        "tracking_number": "FEDX999999999",
        "ordered_days_ago": 8,
        "shipped_days_ago": 7,
        "eta_days_from_now": 5,
        "shipping_address_zip": "10001",
        "is_international": False,
        "is_premium_member": False,
        "contains_clearance_items": False,
        "contains_custom_items": False,
    },
    "PG-1003": {
        "order_id": "PG-1003",
        "customer_id": "cust_003",
        "status": "processing",
        "total": 349.99,
        "items": ["Foldable Exercise Bike"],
        "ordered_days_ago": 3,
        "eta_days_from_now": 4,
        "shipping_address_zip": "33101",
        "is_international": False,
        "is_premium_member": True,
        "contains_clearance_items": False,
        "contains_custom_items": False,
    },
    "PG-1004": {
        "order_id": "PG-1004",
        "customer_id": "cust_004",
        "status": "delivered",
        "total": 59.98,
        "items": ["Premium Lifting Gloves", "Weighted Jump Rope"],
        "carrier": "USPS",
        "tracking_number": "94001111111111111111",
        "ordered_days_ago": 30,
        "shipped_days_ago": 28,
        "delivered_days_ago": 25,
        "shipping_address_zip": "90210",
        "is_international": False,
        "is_premium_member": False,
        "contains_clearance_items": True,
        "contains_custom_items": False,
    },
    "PG-1005": {
        "order_id": "PG-1005",
        "customer_id": "cust_005",
        "status": "returned",
        "total": 129.99,
        "items": ["Adjustable Dumbbells (Pair)"],
        "carrier": "UPS",
        "tracking_number": "1Z8888888888888888",
        "ordered_days_ago": 45,
        "shipped_days_ago": 44,
        "delivered_days_ago": 40,
        "returned_days_ago": 35,
        "shipping_address_zip": "92008",
        "is_international": False,
        "is_premium_member": False,
        "contains_clearance_items": False,
        "contains_custom_items": True,
    },
    "PG-1006": {
        "order_id": "PG-1006",
        "customer_id": "cust_006",
        "status": "delivered",
        "total": 49.99,
        "items": ["High-Waist Performance Leggings"],
        "carrier": "UPS",
        "tracking_number": "1Z7777777777777777",
        "ordered_days_ago": 25,
        "shipped_days_ago": 24,
        "delivered_days_ago": 20,
        "shipping_address_zip": "60601",
        "is_international": False,
        "is_premium_member": False,
        "contains_clearance_items": False,
        "contains_custom_items": False,
    },
    "PG-1007": {
        "order_id": "PG-1007",
        "customer_id": "cust_007",
        "status": "shipped",
        "total": 219.97,
        "items": ["Training Hoodie", "Minimalist Training Shoes"],
        "carrier": "FedEx",
        "tracking_number": "FEDX888888888",
        "ordered_days_ago": 5,
        "shipped_days_ago": 4,
        "eta_days_from_now": 3,
        "shipping_address_zip": "94105",
        "is_international": False,
        "is_premium_member": True,
        "contains_clearance_items": False,
        "contains_custom_items": False,
    },
    "PG-1008": {
        "order_id": "PG-1008",
        "customer_id": "cust_008",
        "status": "cancelled",
        "total": 39.99,
        "items": ["6mm Premium Yoga Mat"],
        "ordered_days_ago": 2,
        "shipping_address_zip": "92008",
        "is_international": False,
        "is_premium_member": False,
        "contains_clearance_items": True,
        "contains_custom_items": False,
    },
    "PG-1009": {
        "order_id": "PG-1009",
        "customer_id": "cust_009",
        "status": "delivered",
        "total": 24.99,
        "items": ["Ab Roller Wheel"],
        "carrier": "USPS",
        "tracking_number": "94002222222222222222",
        "ordered_days_ago": 18,
        "shipped_days_ago": 17,
        "delivered_days_ago": 15,
        "shipping_address_zip": "33139",
        "is_international": False,
        "is_premium_member": False,
        "contains_clearance_items": False,
        "contains_custom_items": False,
    },
    "PG-1010": {
        "order_id": "PG-1010",
        "customer_id": "cust_010",
        "status": "processing",
        "total": 159.97,
        "items": ["Resistance Bands Set", "Training Hoodie", "Water Bottle"],
        "ordered_hours_ago": 6,
        "eta_days_from_now": 5,
        "shipping_address_zip": "92008",
        "is_international": False,
        "is_premium_member": False,
        "contains_clearance_items": False,
        "contains_custom_items": False,
    },
    "PG-1011": {
        "order_id": "PG-1011",
        "customer_id": "cust_011",
        "status": "delivered",
        "total": 299.99,
        "items": ["Foldable Exercise Bike"],
        "carrier": "UPS",
        "tracking_number": "1Z6666666666666666",
        "ordered_days_ago": 70,
        "shipped_days_ago": 68,
        "delivered_days_ago": 60,
        "shipping_address_zip": "10013",
        "is_international": False,
        "is_premium_member": True,
        "contains_clearance_items": False,
        "contains_custom_items": False,
    },
    "PG-1012": {
        "order_id": "PG-1012",
        "customer_id": "cust_012",
        "status": "returned",
        "total": 49.99,
        "items": ["High-Waist Performance Leggings"],
        "carrier": "FedEx",
        "tracking_number": "FEDX777777777",
        "ordered_days_ago": 20,
        "shipped_days_ago": 19,
        "delivered_days_ago": 17,
        "returned_days_ago": 12,
        "shipping_address_zip": "92008",
        "is_international": False,
        "is_premium_member": False,
        "contains_clearance_items": True,
        "contains_custom_items": False,
    },
}

_OFFSET_KEYS = frozenset({
    "ordered_days_ago",
    "ordered_hours_ago",
    "shipped_days_ago",
    "delivered_days_ago",
    "returned_days_ago",
    "eta_days_from_now",
})


def _iso(dt) -> str:
    return dt.replace(microsecond=0).isoformat()


def resolve_mock_order(template: dict[str, Any]) -> dict[str, Any]:
    """Materialize relative date offsets against the reference clock."""
    now = reference_now()
    order = {k: v for k, v in template.items() if k not in _OFFSET_KEYS}

    if "ordered_hours_ago" in template:
        order["ordered_at"] = _iso(now - timedelta(hours=template["ordered_hours_ago"]))
    elif "ordered_days_ago" in template:
        order["ordered_at"] = _iso(now - timedelta(days=template["ordered_days_ago"]))

    if "shipped_days_ago" in template:
        order["shipped_at"] = _iso(now - timedelta(days=template["shipped_days_ago"]))
    else:
        order.setdefault("shipped_at", None)

    if "delivered_days_ago" in template:
        order["delivered_at"] = _iso(now - timedelta(days=template["delivered_days_ago"]))
    else:
        order.setdefault("delivered_at", None)

    if "returned_days_ago" in template:
        order["returned_at"] = _iso(now - timedelta(days=template["returned_days_ago"]))
    else:
        order.setdefault("returned_at", None)

    if "eta_days_from_now" in template:
        order["eta"] = _iso(now + timedelta(days=template["eta_days_from_now"]))
    else:
        order.setdefault("eta", None)

    order.setdefault("carrier", None)
    order.setdefault("tracking_number", None)
    return order


def get_mock_order(order_id: str) -> dict[str, Any] | None:
    template = _MOCK_ORDER_TEMPLATES.get(order_id)
    if template is None:
        return None
    return resolve_mock_order(template)



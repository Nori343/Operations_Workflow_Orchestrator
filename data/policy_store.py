POLICIES = {
"returns": {
"policy_id": "returns_v1",
  "version": "1.1",
  "last_updated": "2026-06-01",
  "summary": "Standard items can be returned within 30 days of delivery if unused and in original condition.",
  "structured_rules": {
    "standard_window_days": 30,
    "premium_window_days": 45,
    
    "non_returnable_item_types": ["clearance", "custom"],
    "non_returnable_statuses": ["processing", "returned", "cancelled"],
    
    "denial_reasons": {
      "non_returnable_item": "Clearance and custom orders are not eligible for return.",
      "past_return_window": "The return window has expired.",
      "invalid_status": "This order cannot be returned in its current status."
    }
  },
  "eligibility": [
    "Must be unused with original tags and packaging attached",
    "Apparel must not show signs of wear",
    "Equipment must not be assembled or used"
  ],
  "customer_steps": [
    "Contact support with order number",
    "Receive return shipping label",
    "Ship item back within 14 days of receiving label"
  ],
  },

  "shipping": {
    "policy_id": "shipping_v1",
    "version": "1.0",
    "last_updated": "2026-05-30",
    "summary": "We ship from Carlsbad, CA with standard and express options. Free shipping on orders over $150.",
    "structured_rules": {
      "standard_days": "3-7",
      "express_days": "2-4",
      "free_shipping_threshold": 150,
      "international_available": True
    },
    "customer_steps": [
      "Orders usually ship within 1-2 business days",
      "Track your order using the link in your confirmation email"
    ]
  },

  "cancellations": {
    "policy_id": "cancellations_v1",
    "version": "1.0",
    "last_updated": "2026-05-30",
    "summary": "Orders can be cancelled within 4 hours of placement. Processed orders may incur a restocking fee.",
    "structured_rules": {
      "full_refund_window_hours": 4,
      "can_cancel_after_processing": True,
      "restocking_fee_percent": 10,
      "restocking_fee_applies_after": "processing"
    },
    "customer_steps": [
      "Contact support immediately with order number",
      "Cancellation not possible once shipped"
    ]
  },

  "damaged_items": {
    "policy_id": "damaged_v1",
    "version": "1.0",
    "last_updated": "2026-05-30",
    "summary": "Damaged or defective items can be replaced or refunded if reported within 7 days with photos.",
    "structured_rules": {
      "report_window_days": 7,
      "requires_photo": True,
      "preferred_solution": "replacement",
      "high_value_priority": True
    },
    "customer_steps": [
      "Take clear photos of damage and packaging",
      "Contact support with order number and photos",
      "We review within 24 hours"
    ],
    "cross_references": ["returns"]
  },

  "missing_package": {
    "policy_id": "missing_package_v1",
    "version": "1.0",
    "last_updated": "2026-05-30",
    "summary": "If package shows delivered but not received, wait 2 days then contact support. We will investigate and reship or refund if lost.",
    "structured_rules": {
      "wait_days_after_delivery_scan": 2,
      "investigation_days": "3-5",
      "high_value_threshold": 150,
      "high_value_priority": True,
      "resolution_options": ["reship_at_no_cost", "full_refund"]
    },
    "customer_steps": [
      "Wait 2 business days after delivered scan",
      "Check with neighbors, apartment office, or porch camera",
      "Contact support with order number"
    ],
    "cross_references": ["shipping"]
  },

  "faqs": {
    "policy_id": "general_faqs_v1",
    "version": "1.0",
    "last_updated": "2026-05-30",
    "summary": "PeakGear Fitness was founded in 2019 in Carlsbad, California. We create premium fitness equipment and apparel.",
    "structured_rules": {},
    "customer_steps": [],
    "company_info": {
      "founded_year": 2019,
      "headquarters": "Carlsbad, CA",
      "mission": "To make premium fitness accessible by combining performance-driven design with fair pricing."
    }
  }
}
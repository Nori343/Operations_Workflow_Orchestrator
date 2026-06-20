"""Reference clock for mock orders and time-based policy checks."""

from __future__ import annotations

import os
from datetime import date, datetime


def reference_now() -> datetime:
    """
    Current time for policy evaluation and mock order resolution.

    Set MOCK_REFERENCE_DATE (YYYY-MM-DD or ISO datetime) to freeze time for stable evals.
    """
    raw = os.getenv("MOCK_REFERENCE_DATE", "").strip()
    if not raw:
        return datetime.now()
    if len(raw) == 10:
        return datetime.fromisoformat(f"{raw}T12:00:00")
    return datetime.fromisoformat(raw)


def reference_today() -> date:
    return reference_now().date()

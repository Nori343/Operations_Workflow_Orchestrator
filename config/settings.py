from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class LLMSettings:
    model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    api_key: str | None = os.getenv("OPENAI_API_KEY")
    timeout_seconds: float = float(os.getenv("OPENAI_TIMEOUT", "30"))
    max_retries: int = int(os.getenv("OPENAI_MAX_RETRIES", "1"))

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

@dataclass(frozen=True)
class RiskSettings:
    high_value_threshold_usd: float = float(os.getenv("RISK_HIGH_VALUE_USD", "500"))

@dataclass(frozen=True)
class Settings:
    llm: LLMSettings = LLMSettings()
    risk: RiskSettings = RiskSettings()
    planner_confidence_threshold: float = float(
        os.getenv("PLANNER_CONFIDENCE_THRESHOLD", "0.67")
    )
    default_thread_prefix: str = "ticket"


settings = Settings()
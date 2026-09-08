"""Provider seam for future assisted reasoning without coupling the demo to an API."""

import os
from dataclasses import dataclass
from typing import Protocol


class ReasoningProvider(Protocol):
    """Minimal contract an optional reasoning provider can implement."""

    mode: str

    def pipeline_note(self) -> str:
        """Describe how the provider participates in a simulation."""


@dataclass(frozen=True)
class DemoReasoningProvider:
    mode: str = "demo"

    def pipeline_note(self) -> str:
        return "Deterministic transparent rules; no external model call."


@dataclass(frozen=True)
class OptionalLLMProvider:
    """Configuration holder for a future server-side provider adapter.

    The primary demo intentionally remains deterministic. A real adapter can implement the
    same protocol behind this object without moving credentials into the browser.
    """

    provider_name: str
    mode: str = "provider"

    def pipeline_note(self) -> str:
        return f"Optional provider configured server-side: {self.provider_name}."


def get_reasoning_provider() -> ReasoningProvider:
    """Select demo mode unless a provider name and server-side key are configured."""

    provider_name = os.getenv("LAWSEER_REASONING_PROVIDER", "demo").strip().lower()
    if provider_name != "demo" and os.getenv("LAWSEER_LLM_API_KEY"):
        return OptionalLLMProvider(provider_name=provider_name)
    return DemoReasoningProvider()

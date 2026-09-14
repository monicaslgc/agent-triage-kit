"""The `LLMClient` seam.

Every agent takes an optional `brain: LLMClient | None`. When `None` (the
default, and what the demo uses), agents fall back to deterministic rules --
which keeps the project runnable offline, fast, and unit-testable.

When you want real model calls, implement this Protocol against whichever
provider you use and pass it in:

    class MyLLM:
        def complete(self, prompt: str) -> str:
            return my_client.messages.create(...).content

    Orchestrator(brain=MyLLM())

No orchestration or agent-selection logic needs to change either way -- the
rule-based path and the model-backed path implement the same interface.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    def complete(self, prompt: str) -> str:
        """Return a text completion for `prompt`."""
        ...

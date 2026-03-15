from __future__ import annotations

from typing import Any, Protocol


class Provider(Protocol):
    def generate(self, role: str, prompt: str) -> dict[str, Any]:
        ...

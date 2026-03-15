from __future__ import annotations

from asd_shop.agent_backends.base import AgentBackend
from asd_shop.agent_backends.claude_cli import ClaudeCliBackend
from asd_shop.agent_backends.codex_cli import CodexCliBackend


def get_backend(name: str) -> AgentBackend:
    if name == "codex":
        return CodexCliBackend()
    if name == "claude":
        return ClaudeCliBackend()
    raise ValueError(f"Unsupported backend: {name}")

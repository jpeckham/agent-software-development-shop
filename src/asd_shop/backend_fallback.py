from __future__ import annotations

from asd_shop.shell_runner import CommandResult


FALLBACK_TOKENS = (
    "out of credits",
    "quota",
    "rate limit",
    "authentication",
    "unauthorized",
    "service unavailable",
    "temporarily unavailable",
)


def should_fallback_to_claude(backend_name: str, result: CommandResult) -> bool:
    if backend_name != "codex" or result.exit_code == 0:
        return False
    combined = f"{result.stdout}\n{result.stderr}".lower()
    return any(token in combined for token in FALLBACK_TOKENS)

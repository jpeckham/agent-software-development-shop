from __future__ import annotations

from pathlib import Path
from typing import Protocol

from asd_shop.shell_runner import CommandResult


class AgentBackend(Protocol):
    name: str

    def build_command(self, prompt: str, workspace: Path) -> list[str]:
        ...

    def run(self, prompt: str, workspace: Path, stage_name: str) -> CommandResult:
        ...

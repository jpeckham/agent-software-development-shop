from __future__ import annotations

from pathlib import Path

from asd_shop.shell_runner import CommandResult, ShellRunner, SubprocessShellRunner


class CodexCliBackend:
    name = "codex"

    def __init__(self, shell_runner: ShellRunner | None = None) -> None:
        self.shell_runner = shell_runner or SubprocessShellRunner()

    def build_command(self, prompt: str, workspace: Path) -> list[str]:
        return [
            "codex",
            "exec",
            "--dangerously-bypass-approvals-and-sandbox",
            "-C",
            str(workspace),
            prompt,
        ]

    def run(self, prompt: str, workspace: Path, stage_name: str) -> CommandResult:
        del stage_name
        return self.shell_runner.run(self.build_command(prompt, workspace), workspace)

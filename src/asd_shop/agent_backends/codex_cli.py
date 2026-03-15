from __future__ import annotations

import os
from pathlib import Path

from asd_shop.agent_backends.interactive_session import parse_codex_json_output
from asd_shop.agent_backends.interactive_session import run_interactive_session
from asd_shop.shell_runner import CommandResult, ShellRunner, SubprocessShellRunner


class CodexCliBackend:
    name = "codex"
    UNSET_ENV = {"CODEX_THREAD_ID"}
    ENV_ALLOWLIST = (
        "APPDATA",
        "COMSPEC",
        "HOMEDRIVE",
        "HOMEPATH",
        "LOCALAPPDATA",
        "PATH",
        "PATHEXT",
        "PROGRAMDATA",
        "PROGRAMFILES",
        "PROGRAMFILES(X86)",
        "SYSTEMDRIVE",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "USERPROFILE",
        "USERNAME",
    )

    def __init__(self, shell_runner: ShellRunner | None = None) -> None:
        self.shell_runner = shell_runner or SubprocessShellRunner()

    def build_command(self, prompt: str, workspace: Path) -> list[str]:
        return [
            "codex",
            "exec",
            "--json",
            "--ephemeral",
            "--dangerously-bypass-approvals-and-sandbox",
            "-C",
            str(workspace),
            prompt,
        ]

    def build_continue_command(self, session_id: str, prompt: str, workspace: Path) -> list[str]:
        return [
            "codex",
            "exec",
            "resume",
            "--json",
            "--dangerously-bypass-approvals-and-sandbox",
            session_id,
            prompt,
        ]

    def _build_environment(self) -> dict[str, str]:
        return {name: value for name in self.ENV_ALLOWLIST if (value := os.environ.get(name)) is not None}

    def run(self, prompt: str, workspace: Path, stage_name: str) -> CommandResult:
        del stage_name
        return run_interactive_session(
            initial_command=lambda: self.build_command(prompt, workspace),
            continue_command=lambda session_id, follow_up: self.build_continue_command(session_id, follow_up, workspace),
            parse_output=parse_codex_json_output,
            execute=lambda args: self.shell_runner.run(
                args,
                workspace,
                unset_env=self.UNSET_ENV,
                inherit_env=False,
                extra_env=self._build_environment(),
            ),
            original_prompt=prompt,
        )

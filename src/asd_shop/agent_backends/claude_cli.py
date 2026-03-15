from __future__ import annotations

import uuid
from pathlib import Path

from asd_shop.agent_backends.interactive_session import InteractiveParseResult
from asd_shop.agent_backends.interactive_session import parse_claude_stream_output
from asd_shop.agent_backends.interactive_session import run_interactive_session
from asd_shop.shell_runner import CommandResult, ShellRunner, SubprocessShellRunner


class ClaudeCliBackend:
    name = "claude"

    def __init__(self, shell_runner: ShellRunner | None = None) -> None:
        self.shell_runner = shell_runner or SubprocessShellRunner()

    def build_command(self, prompt: str, workspace: Path) -> list[str]:
        return self.build_command_for_session(str(uuid.uuid4()), prompt, workspace)

    def build_command_for_session(self, session_id: str, prompt: str, workspace: Path) -> list[str]:
        del workspace
        return [
            "claude",
            "-p",
            "--verbose",
            "--output-format",
            "stream-json",
            "--permission-mode",
            "bypassPermissions",
            "--session-id",
            session_id,
            prompt,
        ]

    def build_continue_command(self, session_id: str, prompt: str, workspace: Path) -> list[str]:
        del workspace
        return [
            "claude",
            "-p",
            "--verbose",
            "--output-format",
            "stream-json",
            "--permission-mode",
            "bypassPermissions",
            "--resume",
            session_id,
            prompt,
        ]

    def run(self, prompt: str, workspace: Path, stage_name: str) -> CommandResult:
        del stage_name
        session_id = str(uuid.uuid4())
        return run_interactive_session(
            initial_command=lambda: self.build_command_for_session(session_id, prompt, workspace),
            continue_command=lambda resumed_session_id, follow_up: self.build_continue_command(
                resumed_session_id,
                follow_up,
                workspace,
            ),
            parse_output=lambda result: InteractiveParseResult(
                session_id=session_id,
                message_text=parse_claude_stream_output(result).message_text,
            ),
            execute=lambda args: self.shell_runner.run(args, workspace),
            original_prompt=prompt,
        )

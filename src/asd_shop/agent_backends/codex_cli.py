from __future__ import annotations

import json
import os
from pathlib import Path

from asd_shop.agent_backends.interactive_session import parse_codex_json_output
from asd_shop.agent_backends.interactive_session import run_interactive_session
from asd_shop.console_events import AgentEventPublisher, agent_display_name, publish_agent_event
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

    def run(
        self,
        prompt: str,
        workspace: Path,
        stage_name: str,
        event_publisher: AgentEventPublisher | None = None,
    ) -> CommandResult:
        output_callback = (
            lambda stream_line: self._publish_output_line(stream_line, stage_name, event_publisher)
            if event_publisher is not None
            else None
        )
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
                output_callback=output_callback,
            ),
            original_prompt=prompt,
        )

    def _publish_output_line(
        self,
        stream_line: tuple[str, str],
        stage_name: str,
        event_publisher: AgentEventPublisher,
    ) -> None:
        stream_name, line = stream_line
        if not line:
            return
        agent_name = agent_display_name(stage_name)
        if stream_name == "stderr":
            publish_agent_event(event_publisher, agent_name=agent_name, level="DEBUG", message=line)
            return
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            publish_agent_event(event_publisher, agent_name=agent_name, level="DEBUG", message=line)
            return
        message = _codex_event_message(item)
        if message is not None:
            publish_agent_event(event_publisher, agent_name=agent_name, level="INFO", message=message)


def _codex_event_message(item: dict[str, object]) -> str | None:
    item_type = item.get("type")
    payload = item.get("item")
    if item_type == "thread.started":
        return "codex thread started"
    if not isinstance(payload, dict):
        return None
    payload_type = payload.get("type")
    if item_type == "item.started" and payload_type == "command_execution":
        command = payload.get("command")
        return f"running command: {command}" if command else "running command"
    if item_type == "item.completed" and payload_type == "agent_message":
        text = payload.get("text")
        return str(text) if text else None
    if item_type == "item.completed" and payload_type == "command_execution":
        command = payload.get("command")
        exit_code = payload.get("exit_code")
        if command is not None and exit_code is not None:
            return f"command completed ({exit_code}): {command}"
    return None

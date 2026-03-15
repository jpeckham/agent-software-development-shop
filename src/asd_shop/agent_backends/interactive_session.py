from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Callable

from asd_shop.shell_runner import CommandResult

WORKTREE_RESPONSE = (
    "Do not use a worktree. Work directly in the current local workspace on a normal feature branch. "
    "If you need isolation, create and use a standard git branch in this repository instead. "
    "Commit and push your changes when complete, then leave that branch checked out in the local workspace."
)
APPROVAL_RESPONSE = (
    "Supervisor approval is granted for execution of the active feature. Proceed now with implementation."
)


@dataclass(frozen=True)
class InteractiveParseResult:
    session_id: str | None
    message_text: str


def determine_auto_response(message_text: str, original_prompt: str) -> str | None:
    lowered = (message_text or "").lower()
    if (
        "i'll stay in this workspace" in lowered
        or "i will not use a worktree" in lowered
        or "i'll work directly in this local repository" in lowered
        or "leave that branch checked out" in lowered
    ):
        return original_prompt
    if "worktree" in lowered:
        return WORKTREE_RESPONSE
    if (
        "what feature should i implement" in lowered
        or "what should i work on" in lowered
        or "send the task you want" in lowered
        or "send the actual task" in lowered
        or "which scope should i execute now" in lowered
        or "which scope should i execute" in lowered
        or "what task" in lowered
    ):
        return (
            "The task is the one already provided by the supervisor. Execute it now.\n\n"
            f"{original_prompt}"
        )
    if "approval artifact" in lowered or "approve to begin implementation" in lowered:
        return APPROVAL_RESPONSE
    return None


def run_interactive_session(
    *,
    initial_command: Callable[[], list[str]],
    continue_command: Callable[[str, str], list[str]],
    parse_output: Callable[[CommandResult], InteractiveParseResult],
    execute: Callable[[list[str]], CommandResult],
    original_prompt: str,
    max_turns: int = 4,
) -> CommandResult:
    command = initial_command()
    outputs: list[str] = []
    errors: list[str] = []
    duration_seconds = 0.0
    current_result: CommandResult | None = None

    for _ in range(max_turns):
        current_result = execute(command)
        outputs.append(current_result.stdout)
        errors.append(current_result.stderr)
        duration_seconds += current_result.duration_seconds

        if current_result.exit_code != 0:
            break

        parsed = parse_output(current_result)
        response = determine_auto_response(parsed.message_text, original_prompt)
        if response is None or parsed.session_id is None:
            break
        command = continue_command(parsed.session_id, response)

    if current_result is None:
        raise RuntimeError("interactive session produced no command result")

    return CommandResult(
        args=current_result.args,
        cwd=current_result.cwd,
        exit_code=current_result.exit_code,
        stdout="\n".join(part for part in outputs if part),
        stderr="\n".join(part for part in errors if part),
        duration_seconds=duration_seconds,
    )


def parse_codex_json_output(result: CommandResult) -> InteractiveParseResult:
    session_id = _extract_session_id_from_codex(result.stderr)
    messages: list[str] = []

    for line in (result.stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("type") == "thread.started":
            session_id = item.get("thread_id", session_id)
        if item.get("type") != "item.completed":
            continue
        payload = item.get("item", {})
        if payload.get("type") == "agent_message":
            text = payload.get("text")
            if text:
                messages.append(text)

    return InteractiveParseResult(session_id=session_id, message_text="\n".join(messages))


def parse_claude_stream_output(result: CommandResult) -> InteractiveParseResult:
    messages: list[str] = []

    for line in (result.stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        item_type = item.get("type")
        if item_type == "assistant":
            for content in item.get("message", {}).get("content", []):
                if content.get("type") == "text" and content.get("text"):
                    messages.append(content["text"])
        if item_type == "result" and item.get("result"):
            messages.append(item["result"])

    return InteractiveParseResult(session_id=None, message_text="\n".join(messages))


def _extract_session_id_from_codex(stderr: str) -> str | None:
    match = re.search(r"session id:\s*([0-9a-f-]+)", stderr, re.IGNORECASE)
    return None if match is None else match.group(1)

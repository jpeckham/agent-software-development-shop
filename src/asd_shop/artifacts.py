from __future__ import annotations

import json
from pathlib import Path

from asd_shop.models import TelemetryEvent
from asd_shop.shell_runner import CommandResult


def write_markdown_artifact(run_dir: Path, filename: str, content: str) -> Path:
    artifact_path = run_dir / filename
    artifact_path.write_text(content, encoding="utf-8")
    return artifact_path


def append_event(run_dir: Path, event: TelemetryEvent) -> Path:
    events_path = run_dir / "events.jsonl"
    with events_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event.model_dump(mode="json"), separators=(",", ":")))
        handle.write("\n")
    return events_path


def append_command_log(
    run_dir: Path,
    stage: str,
    backend: str,
    result: CommandResult,
    changed_files: list[str],
    diff_text: str,
) -> Path:
    log_path = run_dir / "command-log.json"
    payload: list[dict[str, object]] = []
    if log_path.exists():
        payload = json.loads(log_path.read_text(encoding="utf-8"))

    payload.append(
        {
            "stage": stage,
            "backend": backend,
            "args": result.args,
            "cwd": result.cwd,
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration_seconds": result.duration_seconds,
            "changed_files": changed_files,
            "diff_text": diff_text,
        }
    )
    log_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return log_path

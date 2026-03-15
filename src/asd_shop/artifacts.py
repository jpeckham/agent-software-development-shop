from __future__ import annotations

import json
from pathlib import Path

from asd_shop.models import TelemetryEvent


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

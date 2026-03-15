from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from asd_shop.models import RunConfig, RunRecord


def _create_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def _write_run_record(record: RunRecord) -> None:
    payload = record.model_dump(mode="json")
    (record.run_dir / "run.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def initialize_run(config: RunConfig) -> RunRecord:
    runs_dir = config.runs_dir or (config.workspace / "runs")
    runs_dir.mkdir(parents=True, exist_ok=True)

    run_id = _create_run_id()
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    record = RunRecord(
        run_id=run_id,
        workspace=Path(config.workspace),
        run_dir=run_dir,
        status=config.status,
    )
    _write_run_record(record)
    return record


def save_run_record(record: RunRecord) -> None:
    record.updated_at = datetime.now(timezone.utc)
    _write_run_record(record)

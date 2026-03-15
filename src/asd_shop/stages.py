from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from asd_shop.artifacts import append_event, write_markdown_artifact
from asd_shop.models import RunRecord, StageName, StageResult, TelemetryEvent
from asd_shop.prompts import build_prompt
from asd_shop.providers.base import Provider
from asd_shop.roles import ROLE_BY_NAME
from asd_shop.storage import save_run_record


def _stage_name(role: str) -> StageName:
    return StageName(role)


def _render_payload(title: str, payload: dict[str, Any]) -> str:
    return f"# {title}\n\n```json\n{json.dumps(payload, indent=2)}\n```"


def execute_stage(
    role: str,
    record: RunRecord,
    provider: Provider,
    prior_artifacts: dict[str, str],
) -> StageResult:
    stage = _stage_name(role)
    record.current_stage = stage
    save_run_record(record)

    append_event(
        record.run_dir,
        TelemetryEvent(
            actor=role,
            event_type="stage_started",
            metadata={"stage": role},
        ),
    )

    prompt = build_prompt(role=role, workspace=record.workspace, prior_artifacts=prior_artifacts)
    payload = provider.generate(role=role, prompt=prompt)
    definition = ROLE_BY_NAME[role]
    artifact_path = write_markdown_artifact(
        record.run_dir,
        definition.artifact_filename,
        _render_payload(payload.get("title", definition.name), payload),
    )

    if role == "developer":
        implementation_payload = {
            "title": "CLI MVP implementation plan",
            "implementation_plan": payload.get("implementation_plan", []),
            "test_plan": payload.get("test_plan", []),
        }
        write_markdown_artifact(
            record.run_dir,
            "ImplementationPlan.md",
            _render_payload("CLI MVP implementation plan", implementation_payload),
        )

    append_event(
        record.run_dir,
        TelemetryEvent(
            actor=role,
            event_type="stage_completed",
            metadata={"stage": role, "artifact": str(Path(artifact_path).name)},
        ),
    )

    return StageResult(
        stage=stage,
        status="completed",
        artifact_path=artifact_path,
        summary=payload.get("summary", payload.get("title")),
    )

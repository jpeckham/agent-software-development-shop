from __future__ import annotations

from asd_shop.models import RunConfig, RunStatus
from asd_shop.providers.base import Provider
from asd_shop.roles import ROLE_DEFINITIONS
from asd_shop.stages import execute_stage
from asd_shop.storage import initialize_run, save_run_record


def run_cycle(config: RunConfig, provider: Provider):
    record = initialize_run(config)
    record.status = RunStatus.RUNNING
    save_run_record(record)

    prior_artifacts: dict[str, str] = {}

    for definition in ROLE_DEFINITIONS:
        result = execute_stage(
            role=definition.name,
            record=record,
            provider=provider,
            prior_artifacts=prior_artifacts,
        )
        if result.artifact_path is not None:
            prior_artifacts[result.artifact_path.name] = result.artifact_path.read_text(encoding="utf-8")

    record.status = RunStatus.READY_FOR_APPROVAL
    save_run_record(record)
    return record

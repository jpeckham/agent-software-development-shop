from __future__ import annotations

from asd_shop.artifacts import append_event
from asd_shop.models import RunConfig, RunStatus, StageName, TelemetryEvent
from asd_shop.roles import ROLE_DEFINITIONS
from asd_shop.stages import execute_stage
from asd_shop.storage import find_most_recent_resumable_run, initialize_run, save_run_record


def _load_prior_artifacts(record):
    prior_artifacts: dict[str, str] = {}
    for definition in ROLE_DEFINITIONS:
        artifact_path = record.run_dir / definition.artifact_filename
        if artifact_path.exists():
            prior_artifacts[artifact_path.name] = artifact_path.read_text(encoding="utf-8")
    implementation_plan = record.run_dir / "ImplementationPlan.md"
    if implementation_plan.exists():
        prior_artifacts[implementation_plan.name] = implementation_plan.read_text(encoding="utf-8")
    return prior_artifacts


def run_cycle(config: RunConfig, *, new_run: bool = False):
    runs_dir = config.runs_dir or (config.workspace / "runs")
    record = None if new_run else find_most_recent_resumable_run(runs_dir)
    if record is None:
        record = initialize_run(config)

    record.status = RunStatus.RUNNING
    save_run_record(record)

    prior_artifacts: dict[str, str] = _load_prior_artifacts(record)
    start_index = 0
    if record.failed_stage is not None:
        start_index = next(
            (index for index, definition in enumerate(ROLE_DEFINITIONS) if definition.name == record.failed_stage.value),
            0,
        )

    for definition in ROLE_DEFINITIONS[start_index:]:
        try:
            result = execute_stage(
                role=definition.name,
                record=record,
                prior_artifacts=prior_artifacts,
            )
        except Exception as error:
            record.status = RunStatus.FAILED
            record.failed_stage = StageName(definition.name)
            append_event(
                record.run_dir,
                TelemetryEvent(
                    actor=definition.name,
                    event_type="stage_failed",
                    metadata={"stage": definition.name, "error": str(error)},
                ),
            )
            save_run_record(record)
            return record
        if result.artifact_path is not None:
            prior_artifacts[result.artifact_path.name] = result.artifact_path.read_text(encoding="utf-8")

    record.status = RunStatus.READY_FOR_APPROVAL
    record.failed_stage = None
    save_run_record(record)
    return record

from __future__ import annotations

from pathlib import Path

from asd_shop.artifacts import append_command_log, append_event, write_markdown_artifact
from asd_shop.backend_fallback import should_fallback_to_claude
from asd_shop.backend_registry import get_backend
from asd_shop.git_audit import diff_summary
from asd_shop.models import RunRecord, StageName, StageResult, TelemetryEvent
from asd_shop.prompts import build_prompt
from asd_shop.roles import ROLE_BY_NAME
from asd_shop.storage import save_run_record


class StageExecutionError(RuntimeError):
    pass


GENERIC_STARTUP_MARKERS = (
    "send the task you want",
    "developer role is active",
    "operating in `qa` role",
    "what needs qa",
    "i'll apply the relevant skills before touching code",
)


def _stage_name(role: str) -> StageName:
    return StageName(role)


def _is_generic_startup_text(content: str) -> bool:
    lowered = content.lower()
    return any(marker in lowered for marker in GENERIC_STARTUP_MARKERS)


def _has_valid_stage_output(record: RunRecord, role: str, content: str) -> bool:
    definition = ROLE_BY_NAME[role]
    workspace_artifact = record.workspace / definition.artifact_filename
    if workspace_artifact.exists():
        return True
    if definition.artifact_filename in content and not _is_generic_startup_text(content):
        return True
    return False


def _write_stage_artifact(record: RunRecord, role: str, content: str) -> Path:
    definition = ROLE_BY_NAME[role]
    artifact_text = content if content.strip() else f"# {role}\n"
    artifact_path = write_markdown_artifact(record.run_dir, definition.artifact_filename, artifact_text)
    if role == "developer":
        write_markdown_artifact(record.run_dir, "ImplementationPlan.md", artifact_text)
    return artifact_path


def _build_human_approval_packet(prior_artifacts: dict[str, str]) -> str:
    sections = [
        "# Approval Packet",
        "",
        "This packet was generated locally by the supervisor for human review.",
        "",
        "## Included Artifacts",
    ]
    for name in sorted(prior_artifacts):
        sections.append(f"- {name}")
    sections.extend(
        [
            "",
            "## Decision",
            "- Approve",
            "- Approve with changes",
            "- Defer",
            "- Reject",
        ]
    )
    return "\n".join(sections)


def execute_stage(
    role: str,
    record: RunRecord,
    prior_artifacts: dict[str, str],
) -> StageResult:
    stage = _stage_name(role)
    definition = ROLE_BY_NAME[role]
    record.current_stage = stage
    save_run_record(record)

    append_event(
        record.run_dir,
        TelemetryEvent(actor=role, event_type="stage_started", metadata={"stage": role}),
    )

    if role == "human_approval":
        artifact_path = _write_stage_artifact(record, role, _build_human_approval_packet(prior_artifacts))
        append_event(
            record.run_dir,
            TelemetryEvent(
                actor=role,
                event_type="stage_completed",
                metadata={"stage": role, "artifact": artifact_path.name, "backend": "supervisor"},
            ),
        )
        return StageResult(
            stage=stage,
            status="completed",
            artifact_path=artifact_path,
            summary="completed via supervisor",
        )

    last_result = None
    used_backend = None
    for backend_name in definition.backends:
        prompt = build_prompt(
            role=role,
            workspace=record.workspace,
            prior_artifacts=prior_artifacts,
            backend_name=backend_name,
        )
        backend = get_backend(backend_name)
        result = backend.run(prompt=prompt, workspace=record.workspace, stage_name=role)
        audit = diff_summary(record.workspace)
        append_command_log(record.run_dir, role, backend_name, result, audit.changed_files, audit.diff_text)
        (record.run_dir / "git-diff.patch").write_text(audit.diff_text, encoding="utf-8")
        last_result = result
        used_backend = backend_name

        if result.exit_code == 0 and _has_valid_stage_output(record, role, result.stdout):
            artifact_path = _write_stage_artifact(record, role, result.stdout)
            append_event(
                record.run_dir,
                TelemetryEvent(
                    actor=role,
                    event_type="stage_completed",
                    metadata={"stage": role, "artifact": artifact_path.name, "backend": backend_name},
                ),
            )
            return StageResult(
                stage=stage,
                status="completed",
                artifact_path=artifact_path,
                summary=f"completed via {backend_name}",
            )

        if result.exit_code == 0:
            break

        if not should_fallback_to_claude(backend_name, result):
            break

    append_event(
        record.run_dir,
        TelemetryEvent(
            actor=role,
            event_type="stage_failed",
            metadata={
                "stage": role,
                "backend": used_backend,
                "exit_code": None if last_result is None else last_result.exit_code,
            },
        ),
    )
    raise StageExecutionError(f"Stage {role} failed")

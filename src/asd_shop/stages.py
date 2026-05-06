from __future__ import annotations

import inspect
from datetime import timedelta
from pathlib import Path
from time import perf_counter

from asd_shop.artifacts import append_command_log, append_event, write_markdown_artifact
from asd_shop.backend_fallback import should_fallback_to_claude
from asd_shop.backend_registry import get_backend
from asd_shop.console_events import AgentEventPublisher, agent_display_name, publish_agent_event
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
    "i will not use a worktree",
    "i'll stay in this workspace",
    "i'll work directly in this local repository",
    "leave that branch checked out",
)
NON_IMPLEMENTATION_PATH_PREFIXES = ("runs/",)
NON_IMPLEMENTATION_FILENAMES = {
    "ApprovalPacket.md",
    "ArchitectureDecision.md",
    "FeatureProposal.md",
    "FeatureSpec.md",
    "ProjectSnapshot.md",
    "TechnicalDesign.md",
    "QAReport.md",
    "command-log.json",
    "events.jsonl",
    "git-diff.patch",
    "run.json",
}
STAGE_ARTIFACT_ALIASES = {
    "architect": ("FeatureArchitecture.md",),
    "business_analyst": ("BusinessAnalysis.md",),
}


def _stage_name(role: str) -> StageName:
    return StageName(role)


def _is_generic_startup_text(content: str) -> bool:
    lowered = content.lower()
    return any(marker in lowered for marker in GENERIC_STARTUP_MARKERS)


def _has_meaningful_implementation_changes(changed_files: list[str]) -> bool:
    for path in changed_files:
        normalized = path.replace("\\", "/")
        if normalized in NON_IMPLEMENTATION_FILENAMES:
            continue
        if any(normalized.startswith(prefix) for prefix in NON_IMPLEMENTATION_PATH_PREFIXES):
            continue
        return True
    return False


def _has_valid_stage_output(record: RunRecord, role: str, content: str, changed_files: list[str]) -> bool:
    definition = ROLE_BY_NAME[role]
    workspace_artifact = _find_workspace_stage_artifact(record, role)
    if workspace_artifact.exists():
        return True
    if definition.artifact_filename in content and not _is_generic_startup_text(content):
        return True
    if any(alias in content for alias in STAGE_ARTIFACT_ALIASES.get(role, ())) and not _is_generic_startup_text(content):
        return True
    if role == "developer" and _has_meaningful_implementation_changes(changed_files):
        return True
    return False


def _synthesize_developer_artifact(changed_files: list[str], content: str) -> str:
    sections = [
        "# Technical Design",
        "",
        "This artifact was synthesized locally because the developer stage made meaningful repository changes.",
        "",
        "## Changed Files",
    ]
    for path in changed_files:
        normalized = path.replace("\\", "/")
        if normalized in NON_IMPLEMENTATION_FILENAMES:
            continue
        if any(normalized.startswith(prefix) for prefix in NON_IMPLEMENTATION_PATH_PREFIXES):
            continue
        sections.append(f"- {normalized}")
    if content.strip():
        sections.extend(["", "## Backend Output", content.strip()])
    return "\n".join(sections)


def _write_stage_artifact(record: RunRecord, role: str, content: str | None, changed_files: list[str]) -> Path:
    definition = ROLE_BY_NAME[role]
    workspace_artifact = _find_workspace_stage_artifact(record, role)

    if workspace_artifact.exists():
        artifact_text = workspace_artifact.read_text(encoding="utf-8")
    elif content and content.strip():
        artifact_text = content
    else:
        artifact_text = f"# {role}\n"

    if role == "developer" and _has_meaningful_implementation_changes(changed_files) and not workspace_artifact.exists():
        artifact_text = _synthesize_developer_artifact(changed_files, content)
    artifact_path = write_markdown_artifact(record.run_dir, definition.artifact_filename, artifact_text)
    if role == "developer":
        write_markdown_artifact(record.run_dir, "ImplementationPlan.md", artifact_text)
    return artifact_path


def _find_workspace_stage_artifact(record: RunRecord, role: str) -> Path:
    definition = ROLE_BY_NAME[role]
    candidates = [definition.artifact_filename, *STAGE_ARTIFACT_ALIASES.get(role, ())]
    for filename in candidates:
        artifact_path = record.workspace / filename
        if artifact_path.exists():
            return artifact_path
    return record.workspace / definition.artifact_filename


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
    event_publisher: AgentEventPublisher | None = None,
    backend_override: str | None = None,
) -> StageResult:
    started_at = perf_counter()
    stage = _stage_name(role)
    definition = ROLE_BY_NAME[role]
    agent_name = agent_display_name(role)
    record.current_stage = stage
    save_run_record(record)

    publish_agent_event(
        event_publisher,
        agent_name=agent_name,
        level="INFO",
        message=f"task acquisition: starting {role}",
        workflow_id=record.run_id,
    )
    append_event(
        record.run_dir,
        TelemetryEvent(actor=role, event_type="stage_started", metadata={"stage": role}),
    )

    if role == "human_approval":
        publish_agent_event(
            event_publisher,
            agent_name=agent_name,
            level="INFO",
            message="waiting for approval: building approval packet",
            workflow_id=record.run_id,
        )
        artifact_path = _write_stage_artifact(record, role, _build_human_approval_packet(prior_artifacts), [])
        duration = timedelta(seconds=perf_counter() - started_at)
        append_event(
            record.run_dir,
            TelemetryEvent(
                actor=role,
                event_type="stage_completed",
                metadata={"stage": role, "artifact": artifact_path.name, "backend": "supervisor"},
            ),
        )
        publish_agent_event(
            event_publisher,
            agent_name=agent_name,
            level="INFO",
            message=f"completed {role}",
            workflow_id=record.run_id,
            duration=duration,
        )
        return StageResult(
            stage=stage,
            status="completed",
            artifact_path=artifact_path,
            summary="completed via supervisor",
        )

    last_result = None
    used_backend = None
    backend_names = [backend_override] if backend_override is not None else definition.backends
    for attempt_index, backend_name in enumerate(backend_names):
        if attempt_index > 0:
            publish_agent_event(
                event_publisher,
                agent_name=agent_name,
                level="WARNING",
                message=f"retrying {role} with {backend_name}",
                workflow_id=record.run_id,
                retry_count=attempt_index,
            )
        publish_agent_event(
            event_publisher,
            agent_name=agent_name,
            level="INFO",
            message=f"{_operation_name(role)}: running {backend_name}",
            workflow_id=record.run_id,
        )
        prompt = build_prompt(
            role=role,
            workspace=record.workspace,
            prior_artifacts=prior_artifacts,
            backend_name=backend_name,
        )
        backend = get_backend(backend_name)
        result = _run_backend(
            backend,
            prompt=prompt,
            workspace=record.workspace,
            stage_name=role,
            event_publisher=event_publisher,
        )
        audit = diff_summary(record.workspace)
        append_command_log(record.run_dir, role, backend_name, result, audit.changed_files, audit.diff_text)
        (record.run_dir / "git-diff.patch").write_text(audit.diff_text, encoding="utf-8")
        last_result = result
        used_backend = backend_name

        if result.exit_code == 0 and _has_valid_stage_output(record, role, result.stdout, audit.changed_files):
            artifact_path = _write_stage_artifact(record, role, result.stdout, audit.changed_files)
            duration = timedelta(seconds=perf_counter() - started_at)
            append_event(
                record.run_dir,
                TelemetryEvent(
                    actor=role,
                    event_type="stage_completed",
                    metadata={"stage": role, "artifact": artifact_path.name, "backend": backend_name},
                ),
            )
            publish_agent_event(
                event_publisher,
                agent_name=agent_name,
                level="INFO",
                message=f"completed {role}",
                workflow_id=record.run_id,
                duration=duration,
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
    publish_agent_event(
        event_publisher,
        agent_name=agent_name,
        level="ERROR",
        message=f"failure: {role} failed",
        workflow_id=record.run_id,
        duration=timedelta(seconds=perf_counter() - started_at),
    )
    raise StageExecutionError(f"Stage {role} failed")


def _operation_name(role: str) -> str:
    return {
        "repository_analyst": "startup",
        "product_manager": "task acquisition",
        "business_analyst": "spec generation",
        "architect": "planning",
        "developer": "implementation",
        "qa": "test execution",
        "human_approval": "waiting for approval",
    }.get(role, "task acquisition")


def _run_backend(backend, *, prompt: str, workspace: Path, stage_name: str, event_publisher: AgentEventPublisher | None):
    parameters = inspect.signature(backend.run).parameters
    if "event_publisher" in parameters:
        return backend.run(
            prompt=prompt,
            workspace=workspace,
            stage_name=stage_name,
            event_publisher=event_publisher,
        )
    return backend.run(prompt=prompt, workspace=workspace, stage_name=stage_name)

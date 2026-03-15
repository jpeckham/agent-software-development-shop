from __future__ import annotations

from pathlib import Path

from asd_shop.roles import ROLE_BY_NAME


ROLE_EXECUTION_GUIDANCE = {
    "product_manager": [
        "Prefer player-visible or user-visible functionality over pure internal refactors.",
        "Only choose architecture or cleanup work when it directly unlocks or de-risks a near-term user-facing feature.",
    ],
    "developer": [
        "The prior artifacts already define the task.",
        "Do the work now.",
        "Do not ask for the task again.",
        "If you need assumptions, make the smallest reasonable assumptions and continue.",
    ],
    "qa": [
        "The prior artifacts already define the task.",
        "Perform the QA work now.",
        "Do not ask what needs QA.",
        "Produce findings, validation, or execution results immediately.",
    ],
}


def _find_latest_workspace_implementation_plan(workspace: Path) -> Path | None:
    plans_dir = workspace / "docs" / "plans"
    if not plans_dir.exists():
        return None
    candidates = sorted(plans_dir.glob("*implementation*.md"), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def _build_codex_prompt(role: str, workspace: Path, prior_artifacts: dict[str, str]) -> str:
    definition = ROLE_BY_NAME[role]
    sections = [
        "Implement the feature now using the prior artifacts as the task definition.",
        f"Work in this repository: {workspace}",
        f"Required output artifact: {definition.artifact_filename}",
        "Do not ask what the task is.",
        "Do not create or ask for a worktree.",
        "Operate in the current workspace only.",
        "Do not stop at planning or role confirmation.",
        "Make the smallest reasonable assumptions and proceed.",
    ]
    if role == "developer":
        sections.append("Apply code changes in the repository when needed and produce the required artifact.")
        plan_path = _find_latest_workspace_implementation_plan(workspace)
        if plan_path is not None:
            sections.append(f"Execution source of truth: {plan_path}")
            sections.append("Execute Task 1 immediately from that implementation plan.")
            sections.append("Do not re-evaluate whether planning, approval, or worktree setup is needed.")
    elif role == "qa":
        sections.append("Run the relevant verification and produce the required QA artifact immediately.")

    if prior_artifacts:
        sections.append("Read these workspace artifacts before acting:")
        for name in prior_artifacts:
            sections.append(f"- {workspace / name}")
        sections.append("Use those files as the source of truth instead of asking for more context.")

    return "\n\n".join(sections)


def build_prompt(
    role: str,
    workspace: Path,
    prior_artifacts: dict[str, str],
    backend_name: str | None = None,
) -> str:
    if backend_name == "codex" and role in {"developer", "qa"}:
        return _build_codex_prompt(role, workspace, prior_artifacts)

    definition = ROLE_BY_NAME[role]
    sections = [
        f"Role: {definition.name}",
        f"Workspace: {workspace}",
        f"Required artifact file: {definition.artifact_filename}",
        f"Instruction: {definition.instruction}",
        "Write the required artifact file in the workspace or produce complete artifact content on stdout.",
    ]

    for line in ROLE_EXECUTION_GUIDANCE.get(role, []):
        sections.append(line)

    if prior_artifacts:
        sections.append("Prior artifacts:")
        for name, content in prior_artifacts.items():
            sections.append(f"## {name}")
            sections.append(content)

    return "\n\n".join(sections)

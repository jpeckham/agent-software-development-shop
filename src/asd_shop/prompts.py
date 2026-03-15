from __future__ import annotations

from pathlib import Path

from asd_shop.roles import ROLE_BY_NAME


ROLE_EXECUTION_GUIDANCE = {
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


def build_prompt(role: str, workspace: Path, prior_artifacts: dict[str, str]) -> str:
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

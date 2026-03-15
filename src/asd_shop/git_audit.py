from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class DiffSummary:
    changed_files: list[str]
    diff_text: str


def diff_summary(workspace: Path) -> DiffSummary:
    if not (workspace / ".git").exists():
        return DiffSummary(changed_files=[], diff_text="")

    name_only = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=str(workspace),
        capture_output=True,
        text=True,
        check=False,
    )
    patch = subprocess.run(
        ["git", "diff"],
        cwd=str(workspace),
        capture_output=True,
        text=True,
        check=False,
    )
    changed_files = [line for line in name_only.stdout.splitlines() if line]
    return DiffSummary(changed_files=changed_files, diff_text=patch.stdout)

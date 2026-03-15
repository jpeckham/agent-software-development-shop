from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class CommandResult:
    args: list[str]
    cwd: str
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float


class ShellRunner(Protocol):
    def run(self, args: list[str], cwd: Path) -> CommandResult:
        ...


class SubprocessShellRunner:
    def run(self, args: list[str], cwd: Path) -> CommandResult:
        started = time.perf_counter()
        completed = subprocess.run(
            args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )
        duration_seconds = time.perf_counter() - started
        return CommandResult(
            args=args,
            cwd=str(cwd),
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_seconds=duration_seconds,
        )

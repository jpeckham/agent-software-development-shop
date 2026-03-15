from __future__ import annotations

import subprocess
import time
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

WINDOWS = subprocess.os.name == "nt"


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


def resolve_command(command: str) -> str:
    if WINDOWS:
        for candidate in (f"{command}.cmd", f"{command}.exe", command):
            resolved = shutil.which(candidate)
            if resolved:
                return resolved
    resolved = shutil.which(command)
    return resolved or command


class SubprocessShellRunner:
    def run(self, args: list[str], cwd: Path) -> CommandResult:
        started = time.perf_counter()
        resolved_args = [resolve_command(args[0]), *args[1:]]
        completed = subprocess.run(
            resolved_args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )
        duration_seconds = time.perf_counter() - started
        return CommandResult(
            args=resolved_args,
            cwd=str(cwd),
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_seconds=duration_seconds,
        )

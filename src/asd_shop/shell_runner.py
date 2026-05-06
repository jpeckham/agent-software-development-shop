from __future__ import annotations

import os
import subprocess
import time
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

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
    def run(
        self,
        args: list[str],
        cwd: Path,
        unset_env: set[str] | None = None,
        inherit_env: bool = True,
        extra_env: dict[str, str] | None = None,
        output_callback: Callable[[tuple[str, str]], None] | None = None,
    ) -> CommandResult:
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
    def run(
        self,
        args: list[str],
        cwd: Path,
        unset_env: set[str] | None = None,
        inherit_env: bool = True,
        extra_env: dict[str, str] | None = None,
        output_callback: Callable[[tuple[str, str]], None] | None = None,
    ) -> CommandResult:
        started = time.perf_counter()
        resolved_args = [resolve_command(args[0]), *args[1:]]
        environment = dict(os.environ) if inherit_env else {}
        for name in unset_env or set():
            environment.pop(name, None)
        environment.update(extra_env or {})
        if output_callback is None:
            completed = subprocess.run(
                resolved_args,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                env=environment,
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

        process = subprocess.Popen(
            resolved_args,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=environment,
            bufsize=1,
        )
        stdout_parts: list[str] = []
        stderr_parts: list[str] = []
        if process.stdout is not None:
            for line in process.stdout:
                stdout_parts.append(line)
                output_callback(("stdout", line.rstrip("\r\n")))
        stderr_text = process.stderr.read() if process.stderr is not None else ""
        if stderr_text:
            stderr_parts.append(stderr_text)
            for line in stderr_text.splitlines():
                output_callback(("stderr", line))
        exit_code = process.wait()
        duration_seconds = time.perf_counter() - started
        return CommandResult(
            args=resolved_args,
            cwd=str(cwd),
            exit_code=exit_code,
            stdout="".join(stdout_parts),
            stderr="".join(stderr_parts),
            duration_seconds=duration_seconds,
        )

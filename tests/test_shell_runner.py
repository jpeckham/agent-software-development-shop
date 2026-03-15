from pathlib import Path

import asd_shop.shell_runner as shell_runner_module
from asd_shop.shell_runner import CommandResult
from asd_shop.shell_runner import resolve_command


def test_command_result_tracks_exit_code_and_output() -> None:
    result = CommandResult(
        args=["codex", "exec"],
        cwd="C:/repo",
        exit_code=0,
        stdout="ok",
        stderr="",
        duration_seconds=1.2,
    )
    assert result.exit_code == 0
    assert result.stdout == "ok"


def test_resolve_command_prefers_windows_cmd_shim(monkeypatch) -> None:
    monkeypatch.setattr(shell_runner_module, "WINDOWS", True)
    monkeypatch.setattr(
        shell_runner_module.shutil,
        "which",
        lambda command: str(Path("C:/Program Files/nodejs/codex.cmd")) if command == "codex.cmd" else None,
    )
    assert resolve_command("codex") == "C:\\Program Files\\nodejs\\codex.cmd"

from pathlib import Path

import asd_shop.shell_runner as shell_runner_module
from asd_shop.shell_runner import CommandResult
from asd_shop.shell_runner import SubprocessShellRunner
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


def test_subprocess_shell_runner_can_unset_environment_variables(monkeypatch, tmp_path) -> None:
    captured: dict[str, object] = {}

    class Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(args, cwd, capture_output, text, check, env, encoding, errors):
        captured["args"] = args
        captured["cwd"] = cwd
        captured["env"] = env
        captured["encoding"] = encoding
        captured["errors"] = errors
        return Completed()

    monkeypatch.setattr(shell_runner_module, "resolve_command", lambda command: command)
    monkeypatch.setattr(shell_runner_module.subprocess, "run", fake_run)
    monkeypatch.setattr(
        shell_runner_module.os,
        "environ",
        {"CODEX_THREAD_ID": "thread-123", "PATH": "C:\\Windows\\System32"},
    )

    runner = SubprocessShellRunner()
    runner.run(["codex", "exec"], tmp_path, unset_env={"CODEX_THREAD_ID"})

    env = captured["env"]
    assert isinstance(env, dict)
    assert "CODEX_THREAD_ID" not in env
    assert env["PATH"] == "C:\\Windows\\System32"
    assert captured["encoding"] == "utf-8"
    assert captured["errors"] == "replace"


def test_subprocess_shell_runner_can_run_with_explicit_environment_only(monkeypatch, tmp_path) -> None:
    captured: dict[str, object] = {}

    class Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(args, cwd, capture_output, text, check, env, encoding, errors):
        captured["env"] = env
        return Completed()

    monkeypatch.setattr(shell_runner_module, "resolve_command", lambda command: command)
    monkeypatch.setattr(shell_runner_module.subprocess, "run", fake_run)
    monkeypatch.setattr(
        shell_runner_module.os,
        "environ",
        {"CODEX_THREAD_ID": "thread-123", "PATH": "C:\\Windows\\System32", "USERPROFILE": "C:\\Users\\james"},
    )

    runner = SubprocessShellRunner()
    runner.run(
        ["codex", "exec"],
        tmp_path,
        inherit_env=False,
        extra_env={"PATH": "C:\\Windows\\System32"},
    )

    env = captured["env"]
    assert isinstance(env, dict)
    assert env == {"PATH": "C:\\Windows\\System32"}

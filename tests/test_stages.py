from asd_shop.models import RunConfig
from asd_shop.stages import execute_stage
from asd_shop.storage import initialize_run


class FakeBackend:
    def run(self, prompt: str, workspace, stage_name: str):
        from asd_shop.shell_runner import CommandResult

        return CommandResult(
            args=["fake"],
            cwd=str(workspace),
            exit_code=0,
            stdout="# artifact",
            stderr="",
            duration_seconds=0.1,
        )


def test_execute_stage_uses_backend_and_writes_command_log(tmp_path, monkeypatch) -> None:
    record = initialize_run(RunConfig(workspace=tmp_path, runs_dir=tmp_path / "runs"))
    monkeypatch.setattr("asd_shop.stages.get_backend", lambda _: FakeBackend())
    result = execute_stage("repository_analyst", record, prior_artifacts={})
    assert result.status == "completed"
    assert (record.run_dir / "command-log.json").exists()


def test_execute_stage_falls_back_from_codex_to_claude(tmp_path, monkeypatch) -> None:
    record = initialize_run(RunConfig(workspace=tmp_path, runs_dir=tmp_path / "runs"))
    calls = []

    class CodexFailBackend:
        def run(self, prompt: str, workspace, stage_name: str):
            calls.append("codex")
            from asd_shop.shell_runner import CommandResult

            return CommandResult(
                args=["codex", "exec"],
                cwd=str(workspace),
                exit_code=1,
                stdout="",
                stderr="out of credits",
                duration_seconds=0.1,
            )

    class ClaudeBackend:
        def run(self, prompt: str, workspace, stage_name: str):
            calls.append("claude")
            from asd_shop.shell_runner import CommandResult

            return CommandResult(
                args=["claude", "-p"],
                cwd=str(workspace),
                exit_code=0,
                stdout="# artifact",
                stderr="",
                duration_seconds=0.1,
            )

    monkeypatch.setattr(
        "asd_shop.stages.get_backend",
        lambda name: CodexFailBackend() if name == "codex" else ClaudeBackend(),
    )
    result = execute_stage("developer", record, prior_artifacts={})
    assert result.status == "completed"
    assert calls == ["codex", "claude"]

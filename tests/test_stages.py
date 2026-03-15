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
            stdout="`ProjectSnapshot.md` has been written.",
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
                stdout="`TechnicalDesign.md` has been written.",
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


def test_execute_stage_rejects_generic_startup_text(tmp_path, monkeypatch) -> None:
    record = initialize_run(RunConfig(workspace=tmp_path, runs_dir=tmp_path / "runs"))

    class GenericBackend:
        def run(self, prompt: str, workspace, stage_name: str):
            from asd_shop.shell_runner import CommandResult

            return CommandResult(
                args=["codex", "exec"],
                cwd=str(workspace),
                exit_code=0,
                stdout="Developer role is active. Send the task you want implemented.",
                stderr="",
                duration_seconds=0.1,
            )

    monkeypatch.setattr("asd_shop.stages.get_backend", lambda _: GenericBackend())

    from asd_shop.stages import StageExecutionError

    try:
        execute_stage("developer", record, prior_artifacts={})
    except StageExecutionError:
        pass
    else:
        raise AssertionError("expected generic startup text to fail stage validation")


def test_execute_stage_generates_human_approval_locally(tmp_path, monkeypatch) -> None:
    record = initialize_run(RunConfig(workspace=tmp_path, runs_dir=tmp_path / "runs"))

    def fail_if_called(_: str):
        raise AssertionError("human approval should not call any backend")

    monkeypatch.setattr("asd_shop.stages.get_backend", fail_if_called)
    result = execute_stage("human_approval", record, prior_artifacts={"FeatureSpec.md": "# spec"})
    assert result.status == "completed"
    assert result.artifact_path.name == "ApprovalPacket.md"

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


def test_execute_stage_copies_workspace_artifact_when_backend_stdout_is_missing(tmp_path, monkeypatch) -> None:
    record = initialize_run(RunConfig(workspace=tmp_path, runs_dir=tmp_path / "runs"))
    workspace_artifact = tmp_path / "ProjectSnapshot.md"
    workspace_artifact.write_text("# Snapshot", encoding="utf-8")

    class ArtifactOnlyBackend:
        def run(self, prompt: str, workspace, stage_name: str):
            from asd_shop.shell_runner import CommandResult

            return CommandResult(
                args=["claude", "-p"],
                cwd=str(workspace),
                exit_code=0,
                stdout=None,
                stderr="",
                duration_seconds=0.1,
            )

    monkeypatch.setattr("asd_shop.stages.get_backend", lambda _: ArtifactOnlyBackend())

    result = execute_stage("repository_analyst", record, prior_artifacts={})

    assert result.status == "completed"
    assert result.artifact_path is not None
    assert result.artifact_path.read_text(encoding="utf-8") == "# Snapshot"


def test_execute_stage_accepts_business_analysis_alias_for_business_analyst(tmp_path, monkeypatch) -> None:
    record = initialize_run(RunConfig(workspace=tmp_path, runs_dir=tmp_path / "runs"))

    class BusinessAnalystBackend:
        def run(self, prompt: str, workspace, stage_name: str):
            from asd_shop.shell_runner import CommandResult

            (workspace / "BusinessAnalysis.md").write_text("# Business Analysis\n\nStage: business_analyst", encoding="utf-8")
            return CommandResult(
                args=["codex", "exec"],
                cwd=str(workspace),
                exit_code=0,
                stdout="Created BusinessAnalysis.md",
                stderr="",
                duration_seconds=0.1,
            )

    monkeypatch.setattr("asd_shop.stages.get_backend", lambda _: BusinessAnalystBackend())

    result = execute_stage("business_analyst", record, prior_artifacts={}, backend_override="codex")

    assert result.status == "completed"
    assert result.artifact_path is not None
    assert result.artifact_path.name == "FeatureSpec.md"
    assert result.artifact_path.read_text(encoding="utf-8") == "# Business Analysis\n\nStage: business_analyst"


def test_execute_stage_accepts_feature_architecture_alias_for_architect(tmp_path, monkeypatch) -> None:
    record = initialize_run(RunConfig(workspace=tmp_path, runs_dir=tmp_path / "runs"))

    class ArchitectBackend:
        def run(self, prompt: str, workspace, stage_name: str):
            from asd_shop.shell_runner import CommandResult

            (workspace / "FeatureArchitecture.md").write_text(
                "# Feature Architecture\n\nStage: technical_architect",
                encoding="utf-8",
            )
            return CommandResult(
                args=["codex", "exec"],
                cwd=str(workspace),
                exit_code=0,
                stdout="Created FeatureArchitecture.md",
                stderr="",
                duration_seconds=0.1,
            )

    monkeypatch.setattr("asd_shop.stages.get_backend", lambda _: ArchitectBackend())

    result = execute_stage("architect", record, prior_artifacts={}, backend_override="codex")

    assert result.status == "completed"
    assert result.artifact_path is not None
    assert result.artifact_path.name == "ArchitectureDecision.md"
    assert result.artifact_path.read_text(encoding="utf-8") == "# Feature Architecture\n\nStage: technical_architect"


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


def test_execute_stage_rejects_policy_acknowledgement_text(tmp_path, monkeypatch) -> None:
    record = initialize_run(RunConfig(workspace=tmp_path, runs_dir=tmp_path / "runs"))

    class PolicyBackend:
        def run(self, prompt: str, workspace, stage_name: str):
            from asd_shop.shell_runner import CommandResult

            return CommandResult(
                args=["codex", "exec"],
                cwd=str(workspace),
                exit_code=0,
                stdout="I will not use a worktree. I'll work in this repository and leave the branch checked out.",
                stderr="",
                duration_seconds=0.1,
            )

    monkeypatch.setattr("asd_shop.stages.get_backend", lambda _: PolicyBackend())

    from asd_shop.stages import StageExecutionError

    try:
        execute_stage("developer", record, prior_artifacts={})
    except StageExecutionError:
        pass
    else:
        raise AssertionError("expected policy acknowledgement text to fail stage validation")


def test_execute_stage_generates_human_approval_locally(tmp_path, monkeypatch) -> None:
    record = initialize_run(RunConfig(workspace=tmp_path, runs_dir=tmp_path / "runs"))

    def fail_if_called(_: str):
        raise AssertionError("human approval should not call any backend")

    monkeypatch.setattr("asd_shop.stages.get_backend", fail_if_called)
    result = execute_stage("human_approval", record, prior_artifacts={"FeatureSpec.md": "# spec"})
    assert result.status == "completed"
    assert result.artifact_path.name == "ApprovalPacket.md"


def test_execute_stage_accepts_meaningful_developer_code_changes_without_artifact_output(
    tmp_path, monkeypatch
) -> None:
    record = initialize_run(RunConfig(workspace=tmp_path, runs_dir=tmp_path / "runs"))

    class DeveloperBackend:
        def run(self, prompt: str, workspace, stage_name: str):
            from asd_shop.shell_runner import CommandResult

            return CommandResult(
                args=["codex", "exec"],
                cwd=str(workspace),
                exit_code=0,
                stdout="Implementation in progress.",
                stderr="",
                duration_seconds=0.1,
            )

    monkeypatch.setattr("asd_shop.stages.get_backend", lambda _: DeveloperBackend())
    monkeypatch.setattr(
        "asd_shop.stages.diff_summary",
        lambda _: type("Audit", (), {"changed_files": ["src/app.py"], "diff_text": "diff"})(),
    )
    result = execute_stage("developer", record, prior_artifacts={})

    assert result.status == "completed"
    assert result.artifact_path is not None
    assert result.artifact_path.name == "TechnicalDesign.md"
    assert "src/app.py" in result.artifact_path.read_text(encoding="utf-8")

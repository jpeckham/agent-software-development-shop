from asd_shop.models import RunConfig, RunStatus
from asd_shop.shell_runner import CommandResult
from asd_shop.workflow import run_cycle


def test_run_cycle_creates_all_mvp_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "asd_shop.stages.get_backend",
        lambda _: type(
            "Backend",
            (),
            {
                "run": lambda self, prompt, workspace, stage_name: CommandResult(
                    args=["fake"],
                    cwd=str(workspace),
                    exit_code=0,
                    stdout=f"# {stage_name}",
                    stderr="",
                    duration_seconds=0.1,
                )
            },
        )(),
    )
    record = run_cycle(RunConfig(workspace=tmp_path, runs_dir=tmp_path / "runs"))
    assert record.status == RunStatus.READY_FOR_APPROVAL
    for name in [
        "ProjectSnapshot.md",
        "FeatureProposal.md",
        "FeatureSpec.md",
        "ArchitectureDecision.md",
        "TechnicalDesign.md",
        "QAReport.md",
        "ApprovalPacket.md",
    ]:
        assert (record.run_dir / name).exists()

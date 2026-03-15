from asd_shop.models import RunConfig, RunStatus
from asd_shop.shell_runner import CommandResult
from asd_shop.workflow import run_cycle


def test_run_cycle_marks_failed_stage_and_status(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "asd_shop.stages.get_backend",
        lambda _: type(
            "Backend",
            (),
            {
                "run": lambda self, prompt, workspace, stage_name: CommandResult(
                    args=["fake"],
                    cwd=str(workspace),
                    exit_code=1,
                    stdout="",
                    stderr="normal failure",
                    duration_seconds=0.1,
                )
            },
        )(),
    )
    record = run_cycle(RunConfig(workspace=tmp_path, runs_dir=tmp_path / "runs"))
    assert record.status == RunStatus.FAILED
    assert record.failed_stage == "repository_analyst"
    assert (record.run_dir / "events.jsonl").exists()

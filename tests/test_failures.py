from asd_shop.models import RunConfig, RunStatus
from asd_shop.workflow import run_cycle


class FailingProvider:
    def generate(self, role: str, prompt: str):
        raise RuntimeError(f"boom:{role}")


def test_run_cycle_marks_failed_stage_and_status(tmp_path) -> None:
    record = run_cycle(
        config=RunConfig(workspace=tmp_path, runs_dir=tmp_path / "runs"),
        provider=FailingProvider(),
    )
    assert record.status == RunStatus.FAILED
    assert record.failed_stage == "repository_analyst"
    assert (record.run_dir / "events.jsonl").exists()

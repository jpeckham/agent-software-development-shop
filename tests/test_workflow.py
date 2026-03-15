from asd_shop.models import RunConfig, RunStatus
from asd_shop.providers.mock import MockProvider
from asd_shop.workflow import run_cycle


def test_run_cycle_creates_all_mvp_artifacts(tmp_path) -> None:
    record = run_cycle(
        config=RunConfig(workspace=tmp_path, runs_dir=tmp_path / "runs"),
        provider=MockProvider(),
    )
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

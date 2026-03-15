from asd_shop.models import RunConfig
from asd_shop.providers.mock import MockProvider
from asd_shop.stages import execute_stage
from asd_shop.storage import initialize_run


def test_execute_stage_writes_artifact_and_returns_result(tmp_path) -> None:
    record = initialize_run(RunConfig(workspace=tmp_path, runs_dir=tmp_path / "runs"))
    result = execute_stage(
        role="product_manager",
        record=record,
        provider=MockProvider(),
        prior_artifacts={},
    )
    assert result.artifact_path.name == "FeatureProposal.md"
    assert result.status == "completed"

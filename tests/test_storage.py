import json

from asd_shop.models import RunConfig
from asd_shop.storage import initialize_run


def test_initialize_run_creates_run_directory_and_record(tmp_path) -> None:
    config = RunConfig(workspace=tmp_path, runs_dir=tmp_path / "runs")
    record = initialize_run(config)
    assert record.run_dir.exists()
    run_json = record.run_dir / "run.json"
    assert run_json.exists()
    payload = json.loads(run_json.read_text())
    assert payload["status"] == "pending"

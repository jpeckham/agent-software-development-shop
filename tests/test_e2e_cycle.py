import json

from typer.testing import CliRunner

from asd_shop.cli import app


def test_end_to_end_cycle_generates_expected_outputs(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 0
    run_id = sorted(path.name for path in (tmp_path / "runs").iterdir())[-1]
    run_dir = tmp_path / "runs" / run_id
    assert (run_dir / "events.jsonl").exists()
    payload = json.loads((run_dir / "run.json").read_text())
    assert payload["status"] == "ready_for_approval"

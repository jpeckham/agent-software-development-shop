import json

from typer.testing import CliRunner

from asd_shop.cli import app


def test_approve_command_marks_run_approved(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    runner.invoke(app, ["run"])
    runs_dir = tmp_path / "runs"
    run_id = sorted(path.name for path in runs_dir.iterdir())[-1]
    result = runner.invoke(app, ["approve", run_id, "--decision", "approve"])
    assert result.exit_code == 0
    run_json = json.loads((runs_dir / run_id / "run.json").read_text())
    assert run_json["status"] == "approved"

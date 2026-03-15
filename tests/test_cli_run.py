from typer.testing import CliRunner

from asd_shop.cli import app


def test_run_command_executes_cycle(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 0
    assert "ready_for_approval" in result.stdout

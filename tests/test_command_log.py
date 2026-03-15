import json

from asd_shop.artifacts import append_command_log
from asd_shop.shell_runner import CommandResult


def test_append_command_log_writes_json_array_entry(tmp_path) -> None:
    result = CommandResult(
        args=["codex", "exec"],
        cwd=str(tmp_path),
        exit_code=0,
        stdout="ok",
        stderr="",
        duration_seconds=0.5,
    )
    path = append_command_log(tmp_path, "developer", "codex", result, ["README.md"], "diff")
    payload = json.loads(path.read_text())
    assert payload[0]["stage"] == "developer"

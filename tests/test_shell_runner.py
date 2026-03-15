from asd_shop.shell_runner import CommandResult


def test_command_result_tracks_exit_code_and_output() -> None:
    result = CommandResult(
        args=["codex", "exec"],
        cwd="C:/repo",
        exit_code=0,
        stdout="ok",
        stderr="",
        duration_seconds=1.2,
    )
    assert result.exit_code == 0
    assert result.stdout == "ok"

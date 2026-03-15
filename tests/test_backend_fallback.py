from asd_shop.backend_fallback import should_fallback_to_claude
from asd_shop.shell_runner import CommandResult


def test_should_fallback_on_codex_credit_failure() -> None:
    result = CommandResult(
        args=["codex", "exec"],
        cwd="C:/repo",
        exit_code=1,
        stdout="",
        stderr="out of credits",
        duration_seconds=0.2,
    )
    assert should_fallback_to_claude("codex", result) is True


def test_should_not_fallback_on_normal_task_failure() -> None:
    result = CommandResult(
        args=["codex", "exec"],
        cwd="C:/repo",
        exit_code=1,
        stdout="",
        stderr="pytest failed",
        duration_seconds=0.2,
    )
    assert should_fallback_to_claude("codex", result) is False

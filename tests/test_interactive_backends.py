import json
import uuid

from asd_shop.agent_backends.claude_cli import ClaudeCliBackend
from asd_shop.agent_backends.codex_cli import CodexCliBackend
from asd_shop.shell_runner import CommandResult


class SequenceShellRunner:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def run(self, args, cwd, unset_env=None, inherit_env=True, extra_env=None):
        self.calls.append(
            {
                "args": args,
                "cwd": str(cwd),
                "unset_env": unset_env,
                "inherit_env": inherit_env,
                "extra_env": extra_env,
            }
        )
        return self.results.pop(0)


def test_codex_backend_resumes_session_after_worktree_question(tmp_path) -> None:
    runner = SequenceShellRunner(
        [
            CommandResult(
                args=["codex", "exec", "--json"],
                cwd=str(tmp_path),
                exit_code=0,
                stdout=(
                    '{"type":"thread.started","thread_id":"session-123"}\n'
                    '{"type":"item.completed","item":{"type":"agent_message","text":"'
                    "Choose the worktree location: 1. .worktrees/ 2. global"
                    '"}}\n'
                ),
                stderr="",
                duration_seconds=0.1,
            ),
            CommandResult(
                args=["codex", "exec", "resume", "session-123"],
                cwd=str(tmp_path),
                exit_code=0,
                stdout='{"type":"item.completed","item":{"type":"agent_message","text":"`TechnicalDesign.md` has been written."}}\n',
                stderr="",
                duration_seconds=0.1,
            ),
        ]
    )

    backend = CodexCliBackend(shell_runner=runner)
    result = backend.run("implement feature", tmp_path, "developer")

    assert result.exit_code == 0
    assert "`TechnicalDesign.md` has been written." in result.stdout
    assert len(runner.calls) == 2
    assert "--ephemeral" in runner.calls[0]["args"]
    assert runner.calls[1]["args"][:3] == ["codex", "exec", "resume"]
    assert "Do not use a worktree." in runner.calls[1]["args"][-1]


def test_codex_backend_replays_original_prompt_after_policy_ack(tmp_path) -> None:
    runner = SequenceShellRunner(
        [
            CommandResult(
                args=["codex", "exec", "--json"],
                cwd=str(tmp_path),
                exit_code=0,
                stdout='{"type":"thread.started","thread_id":"session-456"}\n{"type":"item.completed","item":{"type":"agent_message","text":"I will not use a worktree and will leave that branch checked out."}}\n',
                stderr="",
                duration_seconds=0.1,
            ),
            CommandResult(
                args=["codex", "exec", "resume", "session-456"],
                cwd=str(tmp_path),
                exit_code=0,
                stdout='{"type":"item.completed","item":{"type":"agent_message","text":"`TechnicalDesign.md` has been written."}}\n',
                stderr="",
                duration_seconds=0.1,
            ),
        ]
    )

    backend = CodexCliBackend(shell_runner=runner)
    result = backend.run("implement feature now", tmp_path, "developer")

    assert result.exit_code == 0
    assert runner.calls[1]["args"][-1] == "implement feature now"


def test_claude_backend_reuses_session_id_for_follow_up(tmp_path, monkeypatch) -> None:
    fixed_session_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    monkeypatch.setattr("asd_shop.agent_backends.claude_cli.uuid.uuid4", lambda: fixed_session_id)

    first_output = "\n".join(
        [
            json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "What feature should I implement?"}]}}),
            json.dumps({"type": "result", "result": "What feature should I implement?"}),
        ]
    )
    second_output = "\n".join(
        [
            json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "`TechnicalDesign.md` has been written."}]}}),
            json.dumps({"type": "result", "result": "`TechnicalDesign.md` has been written."}),
        ]
    )
    runner = SequenceShellRunner(
        [
            CommandResult(args=["claude", "-p"], cwd=str(tmp_path), exit_code=0, stdout=first_output, stderr="", duration_seconds=0.1),
            CommandResult(args=["claude", "-p", "--resume"], cwd=str(tmp_path), exit_code=0, stdout=second_output, stderr="", duration_seconds=0.1),
        ]
    )

    backend = ClaudeCliBackend(shell_runner=runner)
    result = backend.run("implement feature", tmp_path, "developer")

    assert result.exit_code == 0
    assert "`TechnicalDesign.md` has been written." in result.stdout
    assert len(runner.calls) == 2
    assert str(fixed_session_id) in runner.calls[0]["args"]
    assert "--resume" in runner.calls[1]["args"]
    assert str(fixed_session_id) in runner.calls[1]["args"]

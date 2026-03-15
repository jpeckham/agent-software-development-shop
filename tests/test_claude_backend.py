from asd_shop.agent_backends.claude_cli import ClaudeCliBackend


def test_claude_backend_builds_print_command(tmp_path) -> None:
    backend = ClaudeCliBackend()
    command = backend.build_command(prompt="analyze repo", workspace=tmp_path)
    assert command[0] == "claude"
    assert "-p" in command

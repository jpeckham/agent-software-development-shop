from asd_shop.agent_backends.codex_cli import CodexCliBackend


def test_codex_backend_builds_exec_command(tmp_path) -> None:
    backend = CodexCliBackend()
    command = backend.build_command(prompt="implement feature", workspace=tmp_path)
    assert command[0] == "codex"
    assert "exec" in command
    assert "--json" in command
    assert "--ephemeral" in command

import pytest

from asd_shop.shell_runner import CommandResult


@pytest.fixture(autouse=True)
def fake_cli_backends(monkeypatch):
    class FakeBackend:
        def __init__(self, name: str) -> None:
            self.name = name

        def run(self, prompt: str, workspace, stage_name: str) -> CommandResult:
            del prompt
            return CommandResult(
                args=[self.name],
                cwd=str(workspace),
                exit_code=0,
                stdout=f"# {stage_name}",
                stderr="",
                duration_seconds=0.1,
            )

    monkeypatch.setattr("asd_shop.stages.get_backend", lambda name: FakeBackend(name))

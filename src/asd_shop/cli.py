from __future__ import annotations

from pathlib import Path

import typer

from asd_shop.config import Settings
from asd_shop.models import RunConfig
from asd_shop.providers.mock import MockProvider
from asd_shop.providers.openai_compatible import OpenAICompatibleProvider
from asd_shop.workflow import run_cycle

app = typer.Typer(help="Agent Software Development Shop CLI.")


@app.callback()
def main() -> None:
    """Run the CLI command group."""


def _resolve_provider(settings: Settings):
    if settings.provider == "mock":
        return MockProvider()
    return OpenAICompatibleProvider(model=settings.model_name)


@app.command()
def run(workspace: Path = Path(".")) -> None:
    resolved_workspace = workspace.resolve()
    settings = Settings()
    provider = _resolve_provider(settings)
    record = run_cycle(
        config=RunConfig(
            workspace=resolved_workspace,
            runs_dir=(resolved_workspace / settings.runs_dir).resolve(),
        ),
        provider=provider,
    )
    typer.echo(f"run_id={record.run_id}")
    typer.echo(f"status={record.status.value}")

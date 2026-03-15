from __future__ import annotations

from pathlib import Path

import typer

from asd_shop.config import Settings
from asd_shop.artifacts import append_event
from asd_shop.models import RunConfig, RunStatus, TelemetryEvent
from asd_shop.providers.mock import MockProvider
from asd_shop.providers.openai_compatible import OpenAICompatibleProvider
from asd_shop.workflow import run_cycle
from asd_shop.storage import load_run_record, update_run_status

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


@app.command()
def approve(
    run_id: str,
    decision: str = typer.Option(..., "--decision"),
    workspace: Path = Path("."),
) -> None:
    resolved_workspace = workspace.resolve()
    settings = Settings()
    runs_dir = (resolved_workspace / settings.runs_dir).resolve()
    record = load_run_record(runs_dir, run_id)
    status = RunStatus.APPROVED if decision == "approve" else RunStatus.REJECTED
    update_run_status(record, status)
    append_event(
        record.run_dir,
        TelemetryEvent(
            actor="human_approval",
            event_type="approval_recorded",
            metadata={"decision": decision},
        ),
    )
    typer.echo(f"run_id={record.run_id}")
    typer.echo(f"status={status.value}")


if __name__ == "__main__":
    app()

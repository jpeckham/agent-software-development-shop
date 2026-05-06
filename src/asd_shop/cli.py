from __future__ import annotations

from pathlib import Path
from threading import Thread

import typer

from asd_shop.artifacts import append_event
from asd_shop.config import Settings
from asd_shop.console_events import AgentEventPublisher, ConsoleLogRenderer, publish_agent_event
from asd_shop.models import RunConfig, RunStatus, TelemetryEvent
from asd_shop.storage import load_run_record, update_run_status
from asd_shop.workflow import run_cycle

app = typer.Typer(help="Agent Software Development Shop CLI.")


@app.callback()
def main() -> None:
    """Run the CLI command group."""


@app.command()
def run(
    workspace: Path = typer.Argument(
        Path('.'),
        help='Path to the workspace folder to operate on (defaults to current directory).',
    ),
    new_run: bool = typer.Option(False, "--new-run"),
    log_verbosity: str = typer.Option(
        "normal",
        "--log-verbosity",
        help="Console log verbosity: quiet, normal, verbose, or debug.",
    ),
    no_color: bool = typer.Option(False, "--no-color", help="Disable ANSI colors in live agent logs."),
    backend: str | None = typer.Option(
        None,
        "--backend",
        help="Force every stage to use one backend, for example codex or claude.",
    ),
) -> None:
    resolved_workspace = workspace.resolve()
    settings = Settings()
    backend_override = backend or settings.backend
    publisher = AgentEventPublisher()
    renderer = ConsoleLogRenderer(verbosity=log_verbosity, use_color=not no_color)
    publisher.subscribe(renderer.handle)
    record = run_cycle(
        RunConfig(
            workspace=resolved_workspace,
            runs_dir=(resolved_workspace / settings.runs_dir).resolve(),
        ),
        new_run=new_run,
        event_publisher=publisher,
        backend_override=backend_override,
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


@app.command("demo-logs")
def demo_logs(
    log_verbosity: str = typer.Option(
        "normal",
        "--log-verbosity",
        help="Console log verbosity: quiet, normal, verbose, or debug.",
    ),
    no_color: bool = typer.Option(False, "--no-color", help="Disable ANSI colors in demo agent logs."),
) -> None:
    publisher = AgentEventPublisher()
    renderer = ConsoleLogRenderer(verbosity=log_verbosity, use_color=not no_color)
    publisher.subscribe(renderer.handle)

    def emit(agent_name: str, message: str) -> None:
        publish_agent_event(
            publisher,
            agent_name=agent_name,
            level="INFO",
            message=message,
            workflow_id="demo",
        )

    threads = [
        Thread(target=emit, args=("orchestrator", "task acquisition: coordinating workflow")),
        Thread(target=emit, args=("coding-agent", "implementation: writing code")),
        Thread(target=emit, args=("review-agent", "test execution: reviewing changes")),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    app()

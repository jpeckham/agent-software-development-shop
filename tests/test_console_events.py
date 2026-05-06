from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from io import StringIO
from threading import Thread

from asd_shop.console_events import AgentEventPublisher, AgentLogEvent, ConsoleLogRenderer


def test_console_renderer_formats_readable_normal_line_without_color() -> None:
    stream = StringIO()
    renderer = ConsoleLogRenderer(stream=stream, use_color=False)
    event = AgentLogEvent(
        timestamp=datetime(2026, 5, 5, 12, 3, 44, tzinfo=timezone.utc),
        agent_name="coding-agent",
        level="INFO",
        message="running integration tests...",
    )

    renderer.handle(event)

    assert stream.getvalue() == "[12:03:44] [coding-agent] [INFO] running integration tests...\n"


def test_console_renderer_debug_includes_metadata() -> None:
    stream = StringIO()
    renderer = ConsoleLogRenderer(stream=stream, verbosity="debug", use_color=False)
    event = AgentLogEvent(
        timestamp=datetime(2026, 5, 5, 12, 3, 44, tzinfo=timezone.utc),
        agent_name="coding-agent",
        level="INFO",
        message="spec generation completed",
        workflow_id="run-1",
        ticket_id="ticket-7",
        input_tokens=100,
        output_tokens=40,
        estimated_cost=Decimal("0.42"),
        duration=timedelta(seconds=102),
        retry_count=2,
    )

    renderer.handle(event)

    assert stream.getvalue() == (
        "[12:03:44] [coding-agent] [INFO] spec generation completed "
        "duration=00:01:42 retries=2 tokens=100/40 cost=$0.42 "
        "workflow=run-1 ticket=ticket-7\n"
    )


def test_console_renderer_quiet_keeps_errors_only() -> None:
    stream = StringIO()
    renderer = ConsoleLogRenderer(stream=stream, verbosity="quiet", use_color=False)

    renderer.handle(
        AgentLogEvent(
            timestamp=datetime(2026, 5, 5, 12, 0, tzinfo=timezone.utc),
            agent_name="coding-agent",
            level="INFO",
            message="planning...",
        )
    )
    renderer.handle(
        AgentLogEvent(
            timestamp=datetime(2026, 5, 5, 12, 1, tzinfo=timezone.utc),
            agent_name="coding-agent",
            level="ERROR",
            message="tests failed",
        )
    )

    assert stream.getvalue() == "[12:01:00] [coding-agent] [ERROR] tests failed\n"


def test_publisher_delivers_events_to_all_subscribers() -> None:
    publisher = AgentEventPublisher()
    first: list[AgentLogEvent] = []
    second: list[AgentLogEvent] = []
    event = AgentLogEvent(
        timestamp=datetime(2026, 5, 5, 12, 0, tzinfo=timezone.utc),
        agent_name="orchestrator",
        level="INFO",
        message="startup",
    )

    publisher.subscribe(first.append)
    publisher.subscribe(second.append)
    publisher.publish(event)

    assert first == [event]
    assert second == [event]


def test_console_renderer_serializes_concurrent_writes() -> None:
    stream = StringIO()
    renderer = ConsoleLogRenderer(stream=stream, use_color=False)

    def publish_line(index: int) -> None:
        renderer.handle(
            AgentLogEvent(
                timestamp=datetime(2026, 5, 5, 12, 0, index, tzinfo=timezone.utc),
                agent_name="coding-agent",
                level="INFO",
                message=f"line {index}",
            )
        )

    threads = [Thread(target=publish_line, args=(index,)) for index in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    lines = stream.getvalue().splitlines()
    assert len(lines) == 20
    assert all(line.startswith("[12:00:") and line.endswith(tuple(f"line {i}" for i in range(20))) for line in lines)

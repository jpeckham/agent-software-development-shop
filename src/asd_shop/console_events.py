from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from threading import RLock
from typing import Protocol, TextIO


@dataclass(frozen=True)
class AgentLogEvent:
    timestamp: datetime
    agent_name: str
    level: str
    message: str
    workflow_id: str | None = None
    ticket_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost: Decimal | None = None
    duration: timedelta | None = None
    retry_count: int | None = None


class AgentEventSubscriber(Protocol):
    def __call__(self, event: AgentLogEvent) -> None:
        pass


class AgentEventPublisher:
    def __init__(self) -> None:
        self._subscribers: list[AgentEventSubscriber] = []
        self._lock = RLock()

    def subscribe(self, subscriber: AgentEventSubscriber) -> None:
        with self._lock:
            self._subscribers.append(subscriber)

    def publish(self, event: AgentLogEvent) -> None:
        with self._lock:
            subscribers = list(self._subscribers)
        for subscriber in subscribers:
            subscriber(event)


AGENT_COLORS = {
    "orchestrator": "\033[37m",
    "coding-agent": "\033[32m",
    "review-agent": "\033[33m",
    "business-agent": "\033[36m",
    "product-agent": "\033[35m",
    "system": "\033[90m",
}
ERROR_COLOR = "\033[31m"
RESET_COLOR = "\033[0m"

LEVEL_PRIORITY = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
}
VERBOSITY_THRESHOLD = {
    "quiet": 40,
    "normal": 20,
    "verbose": 20,
    "debug": 10,
}


class ConsoleLogRenderer:
    def __init__(
        self,
        *,
        stream: TextIO | None = None,
        verbosity: str = "normal",
        use_color: bool = True,
    ) -> None:
        self.stream = stream or sys.stdout
        self.verbosity = verbosity
        self.use_color = use_color
        self._lock = RLock()

    def handle(self, event: AgentLogEvent) -> None:
        if not self._should_render(event):
            return
        line = self.format(event)
        with self._lock:
            self.stream.write(line)
            self.stream.flush()

    def format(self, event: AgentLogEvent) -> str:
        timestamp = event.timestamp.astimezone(timezone.utc).strftime("%H:%M:%S")
        line = f"[{timestamp}] [{event.agent_name}] [{event.level.upper()}] {event.message}"
        metadata = self._format_metadata(event)
        if metadata:
            line = f"{line} {metadata}"
        if self.use_color:
            line = self._colorize(event, line)
        return f"{line}\n"

    def _should_render(self, event: AgentLogEvent) -> bool:
        threshold = VERBOSITY_THRESHOLD.get(self.verbosity, VERBOSITY_THRESHOLD["normal"])
        priority = LEVEL_PRIORITY.get(event.level.upper(), LEVEL_PRIORITY["INFO"])
        return priority >= threshold

    def _format_metadata(self, event: AgentLogEvent) -> str:
        parts: list[str] = []
        if event.duration is not None and self.verbosity in {"normal", "verbose", "debug"}:
            parts.append(f"duration={_format_duration(event.duration)}")
        if event.retry_count is not None and self.verbosity in {"normal", "verbose", "debug"}:
            parts.append(f"retries={event.retry_count}")
        if (
            event.input_tokens is not None
            and event.output_tokens is not None
            and self.verbosity in {"normal", "verbose", "debug"}
        ):
            parts.append(f"tokens={event.input_tokens}/{event.output_tokens}")
        if event.estimated_cost is not None and self.verbosity in {"normal", "verbose", "debug"}:
            parts.append(f"cost=${event.estimated_cost:.2f}")
        if event.workflow_id is not None and self.verbosity == "debug":
            parts.append(f"workflow={event.workflow_id}")
        if event.ticket_id is not None and self.verbosity == "debug":
            parts.append(f"ticket={event.ticket_id}")
        return " ".join(parts)

    def _colorize(self, event: AgentLogEvent, line: str) -> str:
        color = ERROR_COLOR if event.level.upper() == "ERROR" else AGENT_COLORS.get(event.agent_name)
        if color is None:
            return line
        return f"{color}{line}{RESET_COLOR}"


def publish_agent_event(
    publisher: AgentEventPublisher | None,
    *,
    agent_name: str,
    level: str,
    message: str,
    workflow_id: str | None = None,
    duration: timedelta | None = None,
    retry_count: int | None = None,
) -> None:
    if publisher is None:
        return
    publisher.publish(
        AgentLogEvent(
            timestamp=datetime.now(timezone.utc),
            agent_name=agent_name,
            level=level,
            message=message,
            workflow_id=workflow_id,
            duration=duration,
            retry_count=retry_count,
        )
    )


def agent_display_name(role: str) -> str:
    return {
        "repository_analyst": "orchestrator",
        "product_manager": "product-agent",
        "business_analyst": "business-agent",
        "architect": "orchestrator",
        "developer": "coding-agent",
        "qa": "review-agent",
        "human_approval": "system",
    }.get(role, role)


def _format_duration(duration: timedelta) -> str:
    total_seconds = int(duration.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

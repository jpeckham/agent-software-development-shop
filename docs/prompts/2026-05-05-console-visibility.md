Implement a real-time multi-agent console logging system for the agent runtime.

Goal:
Provide immediate operational visibility into what long-running agents are doing, similar to Docker Compose aggregated container logs.

Repository context:

* This repository is an existing Python CLI package, not a .NET service.
* Implement this inside the current `asd_shop` codebase and Typer CLI.
* Preserve the existing run artifact model, especially `runs/<run-id>/events.jsonl`, while adding live console visibility.
* Do not introduce a new .NET project.

Requirements:

1. Central Console Stream

* All agents must stream logs to a shared console output.
* Each log line must be prefixed with:

  * timestamp
  * agent name
  * log level
* Example:
  [12:03:44] [coding-agent] [INFO] generating implementation plan...

2. Colored Output
   Use consistent colors per agent type:

* orchestrator = white
* coding-agent = green
* review-agent = yellow
* business-agent = cyan
* product-agent = magenta
* system = gray
* errors = red

3. Structured Logging First
   Do NOT build this as scattered raw `print()` or `typer.echo()` calls.

Create a structured event model:

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal


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
```

4. Architecture
   Implement:

* AgentEventPublisher
* AgentEventSubscriber protocol or equivalent interface
* ConsoleLogRenderer
* AgentLogEvent
* CLI options for verbosity and optional color control

Agents publish structured events.
Console renderer subscribes and formats output.

Do NOT tightly couple agents directly to console APIs.

5. Immediate Visibility
   Agents must emit lifecycle events for:

* startup
* shutdown
* task acquisition
* spec generation
* planning
* implementation
* test execution
* deployment
* retries
* failures
* waiting for approval
* completion

6. Human-Friendly Output
   Optimize for readability during long-running sessions.

Good:
[coding-agent] running integration tests...

Bad:
Dumping full prompts or giant JSON blobs.

7. Verbosity Levels
   Support:

* quiet
* normal
* verbose
* debug

Debug mode may emit additional metadata.
Normal mode should remain highly readable.

8. Long-Running Workflow UX
   Add:

* elapsed duration for long operations
* retry counters
* token usage summaries
* estimated cost summaries

Example:
[coding-agent] spec generation completed in 00:01:42 ($0.42)

9. Async Safety
   System must support concurrent agents without mangled console output.
   Use a synchronized rendering pipeline appropriate for Python, such as `queue.Queue`, `asyncio.Queue`, a lock-protected renderer, or a small worker thread.

10. Extensibility
    Design the system so future renderers can be added:

* web dashboard
* OpenTelemetry exporter
* file sink
* Redis/NATS event stream

The console renderer should just be one subscriber.

11. Technology

* Python 3.10+
* Existing Typer CLI
* Existing `asd_shop` package structure
* Existing telemetry artifacts in `runs/<run-id>/`
* Standard library concurrency primitives are preferred unless the repo already has a suitable dependency
* Use dependency injection by passing publisher/renderer objects through workflow and stage functions instead of global console calls

12. Deliverables
    Produce:

* structured event model
* publisher/subscriber interface
* implementation
* integration with the existing workflow and stage execution paths
* CLI options for verbosity
* sample/demo command or test fixture showing multiple agents logging concurrently
* tests covering formatting, verbosity filtering, structured event publication, and concurrency-safe output

13. Demo Scenario
    Create a small demo that simulates:

* orchestrator
* coding-agent
* review-agent

Running concurrently with readable colored output.

Focus on operational clarity and troubleshooting ergonomics over enterprise observability complexity.

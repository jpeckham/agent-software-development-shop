# Codex And Claude CLI Backend Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the current provider-based execution model with direct orchestration of the installed `codex` and `claude` CLIs, allowing autonomous stage execution and repo mutation with full audit logging.

**Architecture:** Introduce backend adapters around `codex exec` and `claude -p`, a shell-runner abstraction for deterministic testing, stage metadata that maps roles to CLIs, and audit capture that records command results plus git diffs after each stage. Preserve the existing workflow structure while swapping the execution engine.

**Tech Stack:** Python 3.10+, Typer, Pydantic v2, pytest, subprocess, git CLI, existing `asd_shop` package.

---

### Task 1: Add a shell-runner abstraction

**Files:**
- Create: `src/asd_shop/shell_runner.py`
- Create: `tests/test_shell_runner.py`

**Step 1: Write the failing test**

```python
from asd_shop.shell_runner import CommandResult


def test_command_result_tracks_exit_code_and_output() -> None:
    result = CommandResult(
        args=["codex", "exec"],
        cwd="C:/repo",
        exit_code=0,
        stdout="ok",
        stderr="",
        duration_seconds=1.2,
    )
    assert result.exit_code == 0
    assert result.stdout == "ok"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_shell_runner.py -v`
Expected: FAIL because `asd_shop.shell_runner` does not exist

**Step 3: Write minimal implementation**

- Add `CommandResult` model or dataclass.
- Add `ShellRunner` protocol.
- Add a concrete subprocess runner that executes commands in a given working directory.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_shell_runner.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asd_shop/shell_runner.py tests/test_shell_runner.py
git commit -m "feat: add shell runner abstraction"
```

### Task 2: Add backend interfaces and Codex CLI adapter

**Files:**
- Create: `src/asd_shop/agent_backends/__init__.py`
- Create: `src/asd_shop/agent_backends/base.py`
- Create: `src/asd_shop/agent_backends/codex_cli.py`
- Create: `tests/test_codex_backend.py`

**Step 1: Write the failing test**

```python
from asd_shop.agent_backends.codex_cli import CodexCliBackend


def test_codex_backend_builds_exec_command(tmp_path) -> None:
    backend = CodexCliBackend()
    command = backend.build_command(prompt="implement feature", workspace=tmp_path)
    assert command[0] == "codex"
    assert "exec" in command
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_codex_backend.py -v`
Expected: FAIL because the backend module does not exist

**Step 3: Write minimal implementation**

- Define a backend protocol with `build_command` and `run`.
- Add `CodexCliBackend` using `codex exec`.
- Include permissive flags consistent with the approved design.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_codex_backend.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asd_shop/agent_backends/__init__.py src/asd_shop/agent_backends/base.py src/asd_shop/agent_backends/codex_cli.py tests/test_codex_backend.py
git commit -m "feat: add codex cli backend"
```

### Task 3: Add Claude CLI adapter

**Files:**
- Create: `src/asd_shop/agent_backends/claude_cli.py`
- Create: `tests/test_claude_backend.py`

**Step 1: Write the failing test**

```python
from asd_shop.agent_backends.claude_cli import ClaudeCliBackend


def test_claude_backend_builds_print_command(tmp_path) -> None:
    backend = ClaudeCliBackend()
    command = backend.build_command(prompt="analyze repo", workspace=tmp_path)
    assert command[0] == "claude"
    assert "-p" in command
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_claude_backend.py -v`
Expected: FAIL because the backend module does not exist

**Step 3: Write minimal implementation**

- Add `ClaudeCliBackend` using `claude -p`.
- Configure flags for non-interactive output and permissive operation in the target repo.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_claude_backend.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asd_shop/agent_backends/claude_cli.py tests/test_claude_backend.py
git commit -m "feat: add claude cli backend"
```

### Task 4: Replace role metadata with backend routing

**Files:**
- Modify: `src/asd_shop/roles.py`
- Create: `tests/test_roles.py`

**Step 1: Write the failing test**

```python
from asd_shop.roles import ROLE_BY_NAME


def test_developer_stage_routes_to_codex() -> None:
    assert ROLE_BY_NAME["developer"].backend == "codex"


def test_repository_analyst_routes_to_claude() -> None:
    assert ROLE_BY_NAME["repository_analyst"].backend == "claude"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_roles.py -v`
Expected: FAIL because backend routing is not defined

**Step 3: Write minimal implementation**

- Extend role definitions with `backend`.
- Route roles according to the approved design.
- Keep artifact filenames intact.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_roles.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asd_shop/roles.py tests/test_roles.py
git commit -m "feat: add backend routing to roles"
```

### Task 5: Add backend registry and selection helpers

**Files:**
- Create: `src/asd_shop/backend_registry.py`
- Create: `tests/test_backend_registry.py`

**Step 1: Write the failing test**

```python
from asd_shop.backend_registry import get_backend


def test_get_backend_returns_codex_backend() -> None:
    backend = get_backend("codex")
    assert backend.__class__.__name__ == "CodexCliBackend"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_backend_registry.py -v`
Expected: FAIL because backend registry does not exist

**Step 3: Write minimal implementation**

- Add a registry that returns the correct backend instance for a backend name.
- Keep the registry simple and local to the current package.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_backend_registry.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asd_shop/backend_registry.py tests/test_backend_registry.py
git commit -m "feat: add backend registry"
```

### Task 6: Add git inspection helpers for changed files and patch capture

**Files:**
- Create: `src/asd_shop/git_audit.py`
- Create: `tests/test_git_audit.py`

**Step 1: Write the failing test**

```python
from asd_shop.git_audit import diff_summary


def test_diff_summary_reports_no_changes_for_clean_repo(tmp_path) -> None:
    summary = diff_summary(tmp_path)
    assert summary.changed_files == []
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_git_audit.py -v`
Expected: FAIL because git audit helpers do not exist

**Step 3: Write minimal implementation**

- Add helpers to collect changed files, diff stats, and full patch text.
- Handle non-git directories defensively.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_git_audit.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asd_shop/git_audit.py tests/test_git_audit.py
git commit -m "feat: add git audit helpers"
```

### Task 7: Add command log persistence

**Files:**
- Modify: `src/asd_shop/artifacts.py`
- Create: `tests/test_command_log.py`

**Step 1: Write the failing test**

```python
import json

from asd_shop.artifacts import append_command_log
from asd_shop.shell_runner import CommandResult


def test_append_command_log_writes_json_array_entry(tmp_path) -> None:
    result = CommandResult(
        args=["codex", "exec"],
        cwd=str(tmp_path),
        exit_code=0,
        stdout="ok",
        stderr="",
        duration_seconds=0.5,
    )
    path = append_command_log(tmp_path, "developer", result, ["README.md"], "diff")
    payload = json.loads(path.read_text())
    assert payload[0]["stage"] == "developer"
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_command_log.py -v`
Expected: FAIL because command logging is not implemented

**Step 3: Write minimal implementation**

- Add a helper to append command execution records to `command-log.json`.
- Record stage, backend, args, cwd, stdout, stderr, exit code, elapsed time, changed files, and diff summary.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_command_log.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asd_shop/artifacts.py tests/test_command_log.py
git commit -m "feat: add command log persistence"
```

### Task 8: Update prompts for CLI backend execution

**Files:**
- Modify: `src/asd_shop/prompts.py`
- Create: `tests/test_backend_prompts.py`

**Step 1: Write the failing test**

```python
from asd_shop.prompts import build_prompt
from asd_shop.roles import ROLE_BY_NAME


def test_build_prompt_includes_expected_artifact_file_for_stage(tmp_path) -> None:
    role = ROLE_BY_NAME["developer"]
    prompt = build_prompt(role=role.name, workspace=tmp_path, prior_artifacts={})
    assert role.artifact_filename in prompt
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_backend_prompts.py -v`
Expected: FAIL because prompts do not include artifact instructions

**Step 3: Write minimal implementation**

- Update prompt building so each stage is instructed which artifact to produce.
- Include backend-friendly execution instructions for Codex and Claude stages.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_backend_prompts.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asd_shop/prompts.py tests/test_backend_prompts.py
git commit -m "feat: update prompts for cli backends"
```

### Task 9: Replace stage execution to use CLI backends

**Files:**
- Modify: `src/asd_shop/stages.py`
- Create: `tests/test_stage_backends.py`

**Step 1: Write the failing test**

```python
from asd_shop.models import RunConfig
from asd_shop.stages import execute_stage
from asd_shop.storage import initialize_run


class FakeBackend:
    def run(self, prompt: str, workspace, stage_name: str):
        from asd_shop.shell_runner import CommandResult
        return CommandResult(
            args=["fake"],
            cwd=str(workspace),
            exit_code=0,
            stdout="# artifact",
            stderr="",
            duration_seconds=0.1,
        )


def test_execute_stage_uses_backend_and_writes_command_log(tmp_path, monkeypatch) -> None:
    record = initialize_run(RunConfig(workspace=tmp_path, runs_dir=tmp_path / "runs"))
    monkeypatch.setattr("asd_shop.stages.get_backend", lambda _: FakeBackend())
    result = execute_stage("repository_analyst", record, prior_artifacts={})
    assert result.status == "completed"
    assert (record.run_dir / "command-log.json").exists()
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_stage_backends.py -v`
Expected: FAIL because stage execution still depends on provider objects

**Step 3: Write minimal implementation**

- Remove the direct provider dependency from stage execution.
- Select the backend from the role definition.
- Run the backend command, write the artifact, command log, and diff patch.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_stage_backends.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asd_shop/stages.py tests/test_stage_backends.py
git commit -m "feat: switch stage execution to cli backends"
```

### Task 10: Update workflow execution for backend-driven stages

**Files:**
- Modify: `src/asd_shop/workflow.py`
- Modify: `tests/test_workflow.py`
- Modify: `tests/test_failures.py`

**Step 1: Write the failing test**

```python
from asd_shop.models import RunConfig, RunStatus
from asd_shop.workflow import run_cycle


def test_run_cycle_marks_ready_for_approval_with_backend_execution(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("asd_shop.stages.get_backend", lambda _: type("B", (), {
        "run": lambda self, prompt, workspace, stage_name: __import__("asd_shop.shell_runner").shell_runner.CommandResult(
            args=["fake"], cwd=str(workspace), exit_code=0, stdout="# artifact", stderr="", duration_seconds=0.1
        )
    })())
    record = run_cycle(RunConfig(workspace=tmp_path, runs_dir=tmp_path / "runs"))
    assert record.status == RunStatus.READY_FOR_APPROVAL
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_workflow.py tests/test_failures.py -v`
Expected: FAIL because workflow still requires an injected provider

**Step 3: Write minimal implementation**

- Remove provider arguments from workflow execution.
- Update failure handling for backend command failures.
- Preserve current stage ordering and run status behavior.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_workflow.py tests/test_failures.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asd_shop/workflow.py tests/test_workflow.py tests/test_failures.py
git commit -m "feat: update workflow for cli backend execution"
```

### Task 11: Remove obsolete provider wiring from CLI and config

**Files:**
- Modify: `src/asd_shop/cli.py`
- Modify: `src/asd_shop/config.py`
- Delete or deprecate: `src/asd_shop/providers/*`
- Modify: `tests/test_cli_run.py`
- Modify: `tests/test_config.py`

**Step 1: Write the failing test**

```python
from asd_shop.config import Settings


def test_settings_no_longer_require_provider_selection() -> None:
    settings = Settings()
    assert hasattr(settings, "runs_dir")
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli_run.py tests/test_config.py -v`
Expected: FAIL while CLI/config still depend on provider selection

**Step 3: Write minimal implementation**

- Remove API-provider selection from the CLI.
- Keep config focused on filesystem and command defaults.
- Remove unused provider modules if they are no longer referenced.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cli_run.py tests/test_config.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/asd_shop/cli.py src/asd_shop/config.py tests/test_cli_run.py tests/test_config.py
git rm -r src/asd_shop/providers
git commit -m "refactor: remove provider-based execution path"
```

### Task 12: Add backend-aware end-to-end tests with mocked shell execution

**Files:**
- Modify: `tests/test_e2e_cycle.py`
- Create: `tests/conftest.py`

**Step 1: Write the failing test**

```python
from typer.testing import CliRunner

from asd_shop.cli import app


def test_end_to_end_cycle_uses_cli_backends(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 0
    assert (tmp_path / "runs").exists()
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_e2e_cycle.py -v`
Expected: FAIL until the shell backend path is fully mocked and wired

**Step 3: Write minimal implementation**

- Add shared fixtures or monkeypatch helpers to fake backend command execution.
- Keep the test deterministic and offline.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_e2e_cycle.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_e2e_cycle.py tests/conftest.py
git commit -m "test: add end-to-end coverage for cli backends"
```

### Task 13: Add manual validation docs for real Codex and Claude CLIs

**Files:**
- Modify: `README.md`

**Step 1: Write the failing test**

No new automated test is required. This task is documentation-only after the backend transition is green.

**Step 2: Run verification commands**

Run: `python -m pytest -v`
Expected: all tests PASS

Run: `python -m asd_shop.cli --help`
Expected: CLI help renders without error

**Step 3: Write minimal implementation**

- Document the installed CLI prerequisites.
- Document how stages route to Codex and Claude.
- Document that stages may mutate the repo directly.
- Document a disposable test-repo validation flow.

**Step 4: Re-run verification**

Run: `python -m pytest -v`
Expected: PASS

**Step 5: Commit**

```bash
git add README.md
git commit -m "docs: describe codex and claude backend setup"
```

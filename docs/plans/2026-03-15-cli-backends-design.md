# Codex And Claude CLI Backend Design

**Date:** 2026-03-15
**Status:** Approved

## Goal

Replace API-key-based LLM execution with direct orchestration of the installed `codex` and `claude` CLIs, allowing autonomous stage execution inside the target repository without intermediate approvals.

## Scope

This design updates the existing CLI MVP so the workflow supervisor shells out to local agent CLIs instead of calling a provider SDK or HTTP API. The supervisor remains responsible for sequencing, prompt construction, status tracking, artifact persistence, and audit logging.

## Execution Model

The application remains a Python CLI supervisor. Each workflow stage is mapped to a backend chain:

- `codex`
- `claude`

Each stage definition includes:

- backend priority list,
- command template,
- prompt text,
- output expectations,
- mutation policy.

The supervisor executes the backend command in the target repository directory. Agents are permitted to modify files directly. There are no intra-run approval prompts in the target repository.

## Recommended Backend Strategy

Use non-interactive CLI modes:

- `codex exec ...`
- `claude -p ...`

This avoids interactive session control complexity and keeps the orchestration logic stable and testable. The supervisor passes role-specific prompts and captures outputs from each invocation independently.

## Stage Routing

The first implementation should use a simple default mapping:

- `repository_analyst` -> `claude`
- `product_manager` -> `claude`
- `business_analyst` -> `claude`
- `architect` -> `claude`
- `developer` -> `codex`, fallback `claude`
- `qa` -> `codex`, fallback `claude`
- `human_approval` -> supervisor-generated packet

This split reflects the likely strength of Claude for document-heavy reasoning and Codex for repository mutation and verification. The mapping should be configurable later.

## Fallback Policy

Any stage whose primary backend is `codex` should automatically fall back to `claude` only when Codex is unavailable for platform reasons such as:

- credits or quota exhausted,
- authentication failure,
- service unavailable,
- transient backend unavailability.

The supervisor must distinguish backend-availability failures from normal task failures. If Codex runs but the task itself fails, the stage remains failed and must not silently switch to Claude.

## Prompt And Output Contract

Prompts remain role-specific and include:

- repository path,
- current run state,
- prior artifact summaries,
- explicit artifact file to produce,
- any backend-specific operating instructions.

In this mode, stage success is not based solely on stdout content. A stage can succeed if:

1. the backend exits with code `0`, and
2. the expected artifact file exists or the supervisor can derive the stage result from command output.

The supervisor should prefer artifact-file outputs over parsing free-form terminal text whenever possible.

## Audit Model

Because mutation is unrestricted, auditability becomes a core requirement. After each stage, the supervisor records:

- exact command,
- backend used,
- working directory,
- stdout,
- stderr,
- exit code,
- elapsed time,
- changed files,
- git diff summary,
- full patch snapshot.

New run outputs:

- `command-log.json`
- `git-diff.patch`

Existing outputs remain:

- stage markdown artifacts,
- `events.jsonl`,
- `run.json`

## Failure Handling

If all eligible backends for a stage fail, or if a stage fails without meeting fallback conditions, the supervisor:

1. records the command result,
2. writes a failure event,
3. updates `run.json` with failed status and stage,
4. stops the cycle,
5. leaves repository changes untouched.

The first version does not attempt rollback or automated cleanup.

## Components

New or updated components:

- `agent_backends/base.py`
- `agent_backends/codex_cli.py`
- `agent_backends/claude_cli.py`
- `shell_runner.py`
- fallback classification for Codex availability failures
- updated stage definitions with backend assignment
- updated workflow execution logic
- git-inspection helpers for changed files and patch capture

The shell runner abstraction is required so tests can mock backend execution without invoking the real CLIs.

## Testing Strategy

Automated tests focus on orchestration and command composition rather than live model behavior.

Key coverage:

- `codex exec` command generation,
- `claude -p` command generation,
- stage-to-backend routing,
- Codex-to-Claude fallback on availability failures,
- no fallback on ordinary task failures,
- failure handling on non-zero exits,
- audit artifact creation,
- diff capture after stage execution,
- end-to-end workflow execution with mocked shell responses.

Manual validation should use a disposable repository and confirm:

- Codex can mutate files through the supervisor,
- Claude can produce analysis artifacts through the supervisor,
- the audit trail captures the actual command behavior.

## Non-Goals

This iteration does not include:

- interactive session reuse,
- rollback of failed stages,
- multi-agent parallel execution in one repository,
- generalized plugin backends,
- cloud or remote execution.

## Future Extensions

Likely follow-on work:

- configurable backend routing,
- persistent session reuse,
- sandbox profiles per stage,
- retry policies,
- rollback and cleanup actions,
- agent capability health checks at startup.

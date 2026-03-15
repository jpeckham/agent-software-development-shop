# Autonomous Agentic Software Development Organization CLI MVP Design

**Date:** 2026-03-15
**Status:** Approved

## Goal

Build a local CLI MVP that runs one autonomous software-development cycle for a target workspace, producing inspectable artifacts, structured telemetry, and a human approval gate.

## Scope

The MVP supports a single-cycle execution model rather than a daemon or continuously running service. It is intended for a single local user and uses real LLM providers through an abstraction layer, with deterministic mock providers for testing.

## MVP Roles

The workflow includes these roles:

- `repository_analyst`
- `product_manager`
- `business_analyst`
- `architect`
- `developer`
- `qa`
- `human_approval`

`repository_analyst` is explicitly in MVP because the quality of downstream decisions depends on an evidence-based project snapshot. Reviewer, release/integration, and security/compliance roles are future extensions.

## Architecture

The application is a Python CLI backed by a small orchestration graph. Each role executes as an explicit workflow stage with well-defined inputs and outputs. The runtime shares a typed `RunContext` that contains configuration, target workspace information, provider access, the current run identifier, artifact paths, and prior stage outputs.

Each stage:

1. Receives normalized structured inputs.
2. Builds a role-specific prompt from templates plus prior artifacts.
3. Calls an LLM provider adapter.
4. Parses the result into a typed artifact model.
5. Writes a human-readable markdown artifact.
6. Emits structured JSONL telemetry.

The graph is linear in the MVP:

`repository_analyst -> product_manager -> business_analyst -> architect -> developer -> qa -> human_approval`

This keeps the first implementation simple while still aligning with the PRD. Later versions can add retries, branching, debate loops, and long-running autonomous iteration.

## CLI Surface

The initial CLI surface is:

- `asd-shop run`
- `asd-shop approve <run-id>`

`asd-shop run` executes one cycle and creates a timestamped run directory under `runs/`. `asd-shop approve <run-id>` records the human approval decision for a completed run. The CLI prints concise stage summaries and the final run status.

## Run Output Structure

Each run creates a directory like `runs/2026-03-15T11-30-00Z/` containing:

- `ProjectSnapshot.md`
- `FeatureProposal.md`
- `FeatureSpec.md`
- `ArchitectureDecision.md`
- `TechnicalDesign.md`
- `ImplementationPlan.md`
- `QAReport.md`
- `ApprovalPacket.md`
- `events.jsonl`
- `run.json`

`run.json` stores normalized run metadata and status. Markdown artifacts are for human inspection. `events.jsonl` is for machine analysis and replay.

## Artifact Responsibilities

- `ProjectSnapshot.md`: repository structure, test inventory, recent activity, risks, opportunities.
- `FeatureProposal.md`: recommended next feature slice and rationale.
- `FeatureSpec.md`: requirements and acceptance criteria.
- `ArchitectureDecision.md`: architectural impact, constraints, and key decisions.
- `TechnicalDesign.md`: implementation structure, APIs, data models, and test strategy.
- `ImplementationPlan.md`: developer-oriented change plan and candidate patch details.
- `QAReport.md`: test outcomes, quality findings, and acceptance-criteria validation.
- `ApprovalPacket.md`: summary for human review with explicit approve/reject guidance.

## Safety Model

The MVP does not silently mutate arbitrary repositories by default. The developer stage generates an implementation packet, including proposed file changes, code snippets, or patch content, rather than applying changes automatically unless an explicit future mode is added. This keeps the first version useful while reducing the risk of unsafe autonomous edits.

## Provider Model

Provider access is hidden behind an adapter interface. The production adapter uses a real LLM provider configured through environment variables. Tests use a deterministic mock adapter that returns fixed structured outputs for each role.

This split allows:

- useful local runs with real models,
- repeatable tests without network calls,
- future support for multiple providers without changing orchestration logic.

## Data Model

Core internal models include:

- `RunConfig`
- `RunContext`
- `RunStatus`
- `StageResult`
- role-specific artifact models
- `TelemetryEvent`

The orchestration layer works with these typed models and converts them into markdown and JSON outputs at the edges.

## Error Handling

The workflow records stage failures instead of crashing without context. If a stage fails due to invalid provider output, parsing failure, or a runtime exception, the CLI:

1. writes a failure event,
2. updates `run.json` with the failed stage and status,
3. emits a readable terminal summary,
4. stops the current cycle.

This is sufficient for the MVP and keeps post-mortem analysis straightforward.

## Testing Strategy

Tests focus on orchestration correctness rather than model quality.

Primary test coverage:

- run directory creation,
- stage ordering,
- artifact creation,
- telemetry emission,
- failure propagation,
- approval state transitions,
- CLI command behavior.

Tests use mock providers so the suite is deterministic and fast. A small number of integration tests can validate real-provider configuration boundaries without depending on live LLM calls.

## Non-Goals

The MVP does not include:

- a web UI,
- continuous autonomous loops,
- multi-branch planning or debate between multiple agents,
- direct GitHub PR creation,
- automatic repository mutation by default,
- advanced security/compliance review.

These can be added once the basic CLI workflow is stable.

## Future Extensions

Likely next additions after MVP:

- reviewer role,
- security/compliance role,
- release/integration role,
- auto-apply mode for safe repositories,
- persistent queue or daemon mode,
- richer approval workflows,
- multi-cycle autonomy.

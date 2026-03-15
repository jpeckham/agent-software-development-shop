# Agent Software Development Shop

This repository contains a local CLI MVP for an autonomous software-development workflow. The tool runs a single multi-agent cycle, writes human-readable artifacts, and records structured telemetry for later review.

## Quickstart

Create a virtual environment, install the project in editable mode with dev dependencies, and run the tests:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
python -m pytest -v
```

## Commands

Run one autonomous cycle in the current directory:

```powershell
python -m asd_shop.cli run
```

Approve the latest run after review:

```powershell
python -m asd_shop.cli approve <run-id> --decision approve
```

Reject a run:

```powershell
python -m asd_shop.cli approve <run-id> --decision reject
```

## Provider Configuration

The default provider is the deterministic mock provider used by the tests. To point the CLI at an OpenAI-compatible endpoint, set:

```powershell
$env:ASD_SHOP_PROVIDER = "openai"
$env:ASD_SHOP_MODEL = "gpt-4.1"
$env:ASD_SHOP_OPENAI_API_KEY = "<token>"
```

Runs are written to `runs/<run-id>/` by default and include markdown artifacts, `run.json`, and `events.jsonl`.

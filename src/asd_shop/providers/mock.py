from __future__ import annotations

from copy import deepcopy


MOCK_RESPONSES = {
    "repository_analyst": {
        "title": "Project snapshot",
        "summary": "Repository contains the CLI MVP scaffold and planning docs.",
        "risks": ["Workflow engine not implemented yet"],
    },
    "product_manager": {
        "title": "CLI MVP feature proposal",
        "summary": "Implement a single autonomous CLI cycle with artifacts and approval.",
        "acceptance_criteria": [
            "CLI run command creates all MVP artifacts",
            "Telemetry is written as JSONL",
            "A human approval command updates run state",
        ],
    },
    "business_analyst": {
        "title": "CLI MVP feature specification",
        "requirements": [
            "Run one cycle locally",
            "Write inspectable markdown artifacts",
            "Track run state and approval status",
        ],
        "acceptance_criteria": ["Cycle completes with ready_for_approval status"],
    },
    "architect": {
        "title": "CLI MVP architecture decision",
        "decision": "Use a linear workflow with typed state and provider adapters.",
    },
    "developer": {
        "title": "CLI MVP technical design",
        "changes": ["Add CLI", "Add workflow runner", "Add telemetry"],
        "test_plan": ["Run pytest", "Run CLI command"],
        "implementation_plan": [
            "Initialize the run directory",
            "Execute each stage in sequence",
            "Write markdown artifacts and JSONL telemetry",
        ],
    },
    "qa": {
        "title": "QA report",
        "summary": "Mock validation passed for the CLI MVP workflow.",
        "quality_score": "green",
    },
    "human_approval": {
        "title": "Approval packet",
        "summary": "The increment is ready for local review.",
        "recommendation": "approve",
    },
}


class MockProvider:
    def generate(self, role: str, prompt: str) -> dict[str, object]:
        del prompt
        try:
            return deepcopy(MOCK_RESPONSES[role])
        except KeyError as error:
            raise ValueError(f"Unsupported mock role: {role}") from error

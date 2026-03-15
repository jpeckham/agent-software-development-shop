from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RoleDefinition:
    name: str
    artifact_filename: str
    instruction: str


ROLE_DEFINITIONS: list[RoleDefinition] = [
    RoleDefinition(
        name="repository_analyst",
        artifact_filename="ProjectSnapshot.md",
        instruction="Analyze the current repository state, risks, and opportunities.",
    ),
    RoleDefinition(
        name="product_manager",
        artifact_filename="FeatureProposal.md",
        instruction="Choose the next highest-value feature slice for the project.",
    ),
    RoleDefinition(
        name="business_analyst",
        artifact_filename="FeatureSpec.md",
        instruction="Write requirements and acceptance criteria for the proposed feature.",
    ),
    RoleDefinition(
        name="architect",
        artifact_filename="ArchitectureDecision.md",
        instruction="Document architectural decisions and impact.",
    ),
    RoleDefinition(
        name="developer",
        artifact_filename="TechnicalDesign.md",
        instruction="Produce a technical design and implementation plan for the feature.",
    ),
    RoleDefinition(
        name="qa",
        artifact_filename="QAReport.md",
        instruction="Evaluate quality, testing posture, and acceptance-criteria readiness.",
    ),
    RoleDefinition(
        name="human_approval",
        artifact_filename="ApprovalPacket.md",
        instruction="Summarize the increment for a human approval decision.",
    ),
]

ROLE_BY_NAME = {definition.name: definition for definition in ROLE_DEFINITIONS}

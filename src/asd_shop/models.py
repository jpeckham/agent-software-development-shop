from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    READY_FOR_APPROVAL = "ready_for_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


class StageName(str, Enum):
    REPOSITORY_ANALYST = "repository_analyst"
    PRODUCT_MANAGER = "product_manager"
    BUSINESS_ANALYST = "business_analyst"
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    QA = "qa"
    HUMAN_APPROVAL = "human_approval"


class RunConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    workspace: Path
    runs_dir: Path | None = None
    status: RunStatus = RunStatus.PENDING


class StageResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    stage: StageName
    status: str
    artifact_path: Path | None = None
    summary: str | None = None


class RunRecord(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    run_id: str
    workspace: Path
    run_dir: Path
    status: RunStatus = RunStatus.PENDING
    current_stage: StageName | None = None
    failed_stage: StageName | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TelemetryEvent(BaseModel):
    actor: str
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    target: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    state_changes: dict[str, Any] = Field(default_factory=dict)

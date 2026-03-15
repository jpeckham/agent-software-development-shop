from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field


class Settings(BaseModel):
    provider: str = Field(default_factory=lambda: os.getenv("ASD_SHOP_PROVIDER", "mock"))
    model_name: str = Field(default_factory=lambda: os.getenv("ASD_SHOP_MODEL", "gpt-4.1"))
    runs_dir: Path = Field(default_factory=lambda: Path(os.getenv("ASD_SHOP_RUNS_DIR", "runs")))

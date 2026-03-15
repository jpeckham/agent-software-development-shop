from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field


class Settings(BaseModel):
    runs_dir: Path = Field(default_factory=lambda: Path(os.getenv("ASD_SHOP_RUNS_DIR", "runs")))

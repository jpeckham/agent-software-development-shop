from __future__ import annotations

import json
import os
from urllib import request


class OpenAICompatibleProvider:
    def __init__(self, model: str, base_url: str | None = None, api_key: str | None = None) -> None:
        self.model = model
        self.base_url = base_url or os.getenv("ASD_SHOP_OPENAI_BASE_URL", "https://api.openai.com/v1/chat/completions")
        self.api_key = api_key or os.getenv("ASD_SHOP_OPENAI_API_KEY", "")

    def generate(self, role: str, prompt: str) -> dict[str, object]:
        payload = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": f"You are acting as {role}."},
                {"role": "user", "content": prompt},
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self.base_url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=60) as response:  # noqa: S310
            raw = json.loads(response.read().decode("utf-8"))
        content = raw["choices"][0]["message"]["content"]
        return json.loads(content)

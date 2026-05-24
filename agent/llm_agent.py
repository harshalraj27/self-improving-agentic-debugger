from __future__ import annotations

from typing import Final

from ollama import Client

_TEMPERATURE: Final[float] = 0.0
_client: Final[Client] = Client()


def query_debugger(
    system_prompt: str,
    user_prompt: str,
    model_name: str = "qwen2.5-coder:7b",
) -> str:
    response = _client.chat(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={"temperature": _TEMPERATURE},
    )
    content = response.message.content
    return content if content is not None else ""

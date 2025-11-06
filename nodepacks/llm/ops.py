from typing import Any


def LLM_Message(role: str, content: str) -> dict[str, Any | dict[str, Any]]:
    return {
        "role": role,
        "content": content,
    }

from typing import Any, Literal


def LLM_Message(
    role: Literal["user", "assistant", "system"], content: str
) -> dict[str, Any | dict[str, Any]]:
    return {
        "role": role,
        "content": content,
    }

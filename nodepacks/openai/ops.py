from typing import Any, Literal


def OpenAI_LLLM_Message(
    role: Literal["user", "assistant", "system", "developer"],
    content: list[dict[str, Any]],
) -> dict[str, Any | dict[str, Any]]:
    return {
        "role": role,
        "content": content,
    }


def create_openai_reponse(
    model: str, messages: list[dict[str, Any]]
) -> dict[str, Any | dict[str, Any]]:
    """
    Create an OpenAI response.

    Args:
        model: The model to use
        messages: The messages to send to the model, can be a string or a list of LLM messages

    Returns:
        The response from the model
    """
    import os

    from openai import OpenAI

    # Check if API key is available in environment
    api_key_present = "OPENAI_API_KEY" in os.environ
    if not api_key_present:
        raise ValueError("OPENAI_API_KEY is not set in the environment")
    client = OpenAI()
    messages = [messages] if isinstance(messages, dict) else messages
    response = client.responses.create(
        model=model, input=messages, stream=False
    ).model_dump()
    return response

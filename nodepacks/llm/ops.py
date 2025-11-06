from typing import Any, Literal


def LLM_Message(
    role: Literal["user", "assistant", "system"], content: str
) -> dict[str, Any | dict[str, Any]]:
    return {
        "role": role,
        "content": content,
    }


def create_openai_reponse(model: str, prompt: str) -> dict[str, Any | dict[str, Any]]:
    """
    Create an OpenAI response.

    Args:
        model: The model to use
        prompt: The prompt to send to the model

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
    response = client.responses.create(model=model, input=prompt).model_dump()
    return response

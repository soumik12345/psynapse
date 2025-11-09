from typing import Any, Literal


def LLM_Message(
    role: Literal["user", "assistant", "system", "developer"], content: str
) -> dict[str, Any | dict[str, Any]]:
    return {
        "role": role,
        "content": content,
    }


def create_openai_reponse(
    model: str, messages: list[dict[str, Any | dict[str, Any]]]
) -> dict[str, Any | dict[str, Any]]:
    """
    Create an OpenAI response.

    Args:
        model: The model to use
        messages: The messages to send to the model

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
    response = client.responses.create(
        model=model, input=messages, stream=False
    ).model_dump()
    return response


def create_litellm_response(
    model: str, messages: list[dict[str, Any | dict[str, Any]]]
) -> dict[str, Any | dict[str, Any]]:
    """
    Create a LiteLLM response.

    Args:
        model: The model to use
        messages: The messages to send to the model

    Returns:
        The response from the model
    """
    from litellm import completion

    response = completion(
        model=model,
        messages=messages,
        stream=False,
    )
    response = response.model_dump()
    return response

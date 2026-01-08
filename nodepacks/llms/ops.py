import os
from typing import Any

from openai import OpenAI


def openai_chat_completion(
    model: str,
    messages: list[dict[str, str | dict[str, str]]],
    base_url: str = "https://api.openai.com/v1",
    api_key_variable: str = "OPENAI_API_KEY",
) -> dict[str, Any]:
    """
    Make a chat completion request to OpenAI.

    Args:
        model (str): The OpenAI model to use.
        messages (list[dict[str, str | dict[str, str]]]): The messages to send to the model.
        base_url (str, optional): The base URL for the OpenAI API. Defaults to "https://api.openai.com/v1".
        api_key_variable (str, optional): The environment variable containing the API key. Defaults to "OPENAI_API_KEY".

    Returns:
        dict[str, Any]: The OpenAI response.
    """
    api_key = os.getenv(api_key_variable)
    if not api_key:
        raise ValueError(
            f"Environment variable '{api_key_variable}' is not set. "
            f"Please set it before running this function."
        )
    client = OpenAI(base_url=base_url, api_key=api_key)
    response = client.chat.completions.create(model=model, messages=messages)
    return response.to_dict()


def get_openai_message_content(response: dict[str, Any]) -> str:
    """Extract the message content from the OpenAI response.

    Args:
        response (dict[str, Any]): The OpenAI response.

    Returns:
        str: The message content.
    """
    return response["choices"][0]["message"]["content"]

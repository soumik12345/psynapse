import os
from typing import Any, Literal

from openai import OpenAI


def openai_chat_completion(
    model: str,
    messages: list[dict[str, str | dict[str, str]]],
    base_url: str = "https://api.openai.com/v1",
    api_key_variable: str = "OPENAI_API_KEY",
    logprobs: bool = False,
    max_completion_tokens: int | None = None,
    max_tokens: int | None = None,
    reasoning_effort: Literal["none", "low", "medium", "high"] | None = None,
    temperature: int | None = None,
    seed: int | None = None,
    top_logprobs: int | None = None,
    top_p: float | None = None,
) -> dict[str, Any]:
    """
    Make a chat completion request to OpenAI.

    Args:
        model (str): The OpenAI model to use.
        messages (list[dict[str, str | dict[str, str]]]): The messages to send to the model.
        base_url (str, optional): The base URL for the OpenAI API. Defaults to "https://api.openai.com/v1".
        api_key_variable (str, optional): The environment variable containing the API key. Defaults to "OPENAI_API_KEY".
        logprobs (bool): Whether to return log probabilities of the output tokens or not. If true,
            returns the log probabilities of each output token returned in the `content` of `message`.
        max_completion_tokens (int | None): An upper bound for the number of tokens that can be generated for a completion,
            including visible output tokens and
            [reasoning tokens](https://platform.openai.com/docs/guides/reasoning).
        max_tokens (int | None): The maximum number of [tokens](/tokenizer) that can be generated in the chat
            completion. This value can be used to control
            [costs](https://openai.com/api/pricing/) for text generated via API.
        reasoning_effort (Literal["none", "low", "medium", "high"] | None): Constrains effort on reasoning for
            [reasoning models](https://platform.openai.com/docs/guides/reasoning). Currently
            supported values are `none`, `minimal`, `low`, `medium`, and `high`. Reducing
            reasoning effort can result in faster responses and fewer tokens used on
            reasoning in a response.
        temperature (int | None): What sampling temperature to use, between 0 and 2. Higher values like 0.8 will
            make the output more random, while lower values like 0.2 will make it more
            focused and deterministic. We generally recommend altering this or `top_p` but
            not both.
        seed (int | None): The seed to use for random number generation. This can be used to make the output
            deterministic.
        top_logprobs (int | None): An integer between 0 and 20 specifying the number of most likely tokens to
            return at each token position, each with an associated log probability.
            `logprobs` must be set to `true` if this parameter is used.
        top_p (float | None): An alternative to sampling with temperature, called nucleus sampling, where the
            model considers the results of the tokens with top_p probability mass. So 0.1
            means only the tokens comprising the top 10% probability mass are considered.
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

    completion_kwargs = {}
    if max_completion_tokens:
        completion_kwargs["max_completion_tokens"] = max_completion_tokens
    if max_tokens:
        completion_kwargs["max_tokens"] = max_tokens
    if reasoning_effort:
        completion_kwargs["reasoning_effort"] = reasoning_effort
    if temperature:
        completion_kwargs["temperature"] = temperature
    if seed:
        completion_kwargs["seed"] = seed
    if top_logprobs:
        completion_kwargs["top_logprobs"] = top_logprobs
    if top_p:
        completion_kwargs["top_p"] = top_p

    response = client.chat.completions.create(
        model=model, messages=messages, logprobs=logprobs, **completion_kwargs
    )
    return response.to_dict()


def get_openai_message_content(response: dict[str, Any]) -> str:
    """Extract the message content from the OpenAI response.

    Args:
        response (dict[str, Any]): The OpenAI response.

    Returns:
        str: The message content.
    """
    return response["choices"][0]["message"]["content"]

import os
from typing import Any, Literal

from psynapse_backend.stateful_op_utils import StreamReporter


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
    from openai import OpenAI

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
        model=model,
        messages=messages,
        logprobs=logprobs,
        stream=False,
        **completion_kwargs,
    )
    return response.to_dict()


def litellm_chat_completion(
    model: str,
    messages: list[dict[str, str | dict[str, str]]],
    temperature: float | None = None,
    top_p: float | None = None,
    max_completion_tokens: int | None = None,
    max_tokens: int | None = None,
    reasoning_effort: Literal["none", "minimal", "low", "medium", "high", "default"]
    | None = None,
    seed: int | None = None,
    logprobs: bool = False,
    base_url: str | None = None,
) -> dict[str, Any]:
    from litellm import completion

    response = completion(
        model=model,
        messages=messages,
        stream=False,
        temperature=temperature,
        top_p=top_p,
        max_completion_tokens=max_completion_tokens,
        max_tokens=max_tokens,
        reasoning_effort=reasoning_effort,
        seed=seed,
        logprobs=logprobs,
        base_url=base_url,
    )
    return response.to_dict()


def get_message_content(response: dict[str, Any]) -> str:
    """Extract the message content from the OpenAI response.

    Args:
        response (dict[str, Any]): The OpenAI response.

    Returns:
        str: The message content.
    """
    return response["choices"][0]["message"]["content"]


class OpenAIChatCompletionStream:
    """
    Make a streaming chat completion request to OpenAI.

    This node streams tokens in real-time to the Execution Status panel,
    allowing you to see the response as it's being generated.

    The final output is a complete response dict matching the non-streaming
    version structure, including usage statistics.
    """

    def __init__(self):
        self._stream_reporter = StreamReporter()

    def __call__(
        self,
        model: str,
        messages: list[dict[str, str | dict[str, str]]],
        base_url: str = "https://api.openai.com/v1",
        api_key_variable: str = "OPENAI_API_KEY",
        max_completion_tokens: int | None = None,
        max_tokens: int | None = None,
        reasoning_effort: Literal["none", "low", "medium", "high"] | None = None,
        temperature: float | None = None,
        seed: int | None = None,
        top_p: float | None = None,
    ) -> dict[str, Any]:
        """
        Make a streaming chat completion request to OpenAI.

        Args:
            model (str): The OpenAI model to use.
            messages (list[dict[str, str | dict[str, str]]]): The messages to send to the model.
            base_url (str, optional): The base URL for the OpenAI API. Defaults to "https://api.openai.com/v1".
            api_key_variable (str, optional): The environment variable containing the API key. Defaults to "OPENAI_API_KEY".
            max_completion_tokens (int | None): An upper bound for the number of tokens that can be generated for a completion.
            max_tokens (int | None): The maximum number of tokens that can be generated in the chat completion.
            reasoning_effort (Literal["none", "low", "medium", "high"] | None): Constrains effort on reasoning for reasoning models.
            temperature (float | None): What sampling temperature to use, between 0 and 2.
            seed (int | None): The seed to use for random number generation.
            top_p (float | None): An alternative to sampling with temperature, called nucleus sampling.

        Returns:
            dict[str, Any]: The OpenAI response with the complete message content.
        """
        from openai import OpenAI

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
        if temperature is not None:
            completion_kwargs["temperature"] = temperature
        if seed:
            completion_kwargs["seed"] = seed
        if top_p is not None:
            completion_kwargs["top_p"] = top_p

        # Make streaming request with stream_options to get usage stats
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            stream_options={"include_usage": True},
            **completion_kwargs,
        )

        # Accumulate the response
        accumulated_content = []
        response_id = None
        response_model = None
        created = None
        finish_reason = None
        usage = None

        for chunk in stream:
            # Capture metadata from first chunk
            if response_id is None and chunk.id:
                response_id = chunk.id
            if response_model is None and chunk.model:
                response_model = chunk.model
            if created is None and chunk.created:
                created = chunk.created

            # Process choices
            if chunk.choices:
                for choice in chunk.choices:
                    if choice.delta and choice.delta.content:
                        content = choice.delta.content
                        accumulated_content.append(content)
                        # Emit the chunk through the stream reporter
                        self._stream_reporter.emit(content)

                    if choice.finish_reason:
                        finish_reason = choice.finish_reason

            # Capture usage from the final chunk
            if chunk.usage:
                usage = {
                    "prompt_tokens": chunk.usage.prompt_tokens,
                    "completion_tokens": chunk.usage.completion_tokens,
                    "total_tokens": chunk.usage.total_tokens,
                }

        # Construct the final response dict matching non-streaming format
        full_content = "".join(accumulated_content)

        response = {
            "id": response_id,
            "object": "chat.completion",
            "created": created,
            "model": response_model or model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": full_content,
                    },
                    "finish_reason": finish_reason or "stop",
                }
            ],
        }

        if usage:
            response["usage"] = usage

        return response

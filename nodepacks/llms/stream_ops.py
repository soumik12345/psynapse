import os
from typing import Any, Callable, Literal, Optional


class _StreamReporter:
    """Context-aware stream reporter for streaming text content."""

    def __init__(self):
        self._callback: Optional[Callable[[str], None]] = None

    def set_callback(self, callback: Callable[[str], None]):
        """Set the callback for stream updates."""
        self._callback = callback

    def emit(self, chunk: str):
        """Emit a text chunk to the stream."""
        if self._callback and chunk:
            self._callback(chunk)


class OpenAIChatCompletionStream:
    """
    Make a streaming chat completion request to OpenAI.

    This node streams tokens in real-time to the Execution Status panel,
    allowing you to see the response as it's being generated.

    The final output is a complete response dict matching the non-streaming
    version structure, including usage statistics.
    """

    def __init__(self):
        self._stream_reporter = _StreamReporter()

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

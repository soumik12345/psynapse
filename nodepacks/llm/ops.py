from typing import Any, Dict, List, Literal


def LLM_Message(
    role: Literal["user", "assistant", "system", "developer"],
    content: list[dict[str, Any]],
) -> dict[str, Any | dict[str, Any]]:
    return {
        "role": role,
        "content": content,
    }


def create_openai_reponse(
    model: str,
    messages: str | list[dict[str, Any]],
    schema: dict | None = None,
    base_url: str = "https://api.openai.com/v1",
    api_key_secret: str = "OPENAI_API_KEY",
    enable_image_generation: bool = False,
) -> Any:
    """
    Create an OpenAI response.

    Args:
        model: The model to use
        messages: The messages to send to the model, can be a string or a list of LLM messages
        schema: The schema to use for the response
        base_url: The base URL to use for the API
        api_key_secret: The secret to use for the API key
        enable_image_generation: Whether to enable image generation

    Returns:
        The response from the model
    """
    import base64
    import os
    from io import BytesIO

    from openai import OpenAI
    from PIL import Image
    from pydantic import BaseModel, create_model

    def json_schema_type_to_py_type(schema: dict) -> Any:
        """JSON-schema → Python type mapper."""
        t = schema.get("type")

        if t == "string":
            return str
        if t == "integer":
            return int
        if t == "number":
            return float
        if t == "boolean":
            return bool
        if t == "array":
            item_schema = schema.get("items") or {}
            item_type = json_schema_type_to_py_type(item_schema) if item_schema else Any
            return List[item_type]
        if t == "object":
            return Dict[str, Any]

        # Fallback
        return Any

    def pydantic_model_from_schema_dict(schema_dict: dict) -> type[BaseModel]:
        if schema_dict.get("__type__") != "PydanticModelType":
            raise ValueError("Not a PydanticModelType schema")

        model_name = schema_dict["model_name"]
        json_schema = schema_dict["json_schema"]

        properties: dict = json_schema.get("properties", {})
        required_fields = set(json_schema.get("required", []))

        # Build fields for create_model: {name: (type, default_or_ellipsis)}
        fields = {}
        for field_name, field_schema in properties.items():
            py_type = json_schema_type_to_py_type(field_schema)
            default = ... if field_name in required_fields else None
            fields[field_name] = (py_type, default)

        # Dynamically create model class
        schema = create_model(model_name, **fields)  # type: ignore[arg-type]
        return schema

    # Check if API key is available in environment
    api_key_present = api_key_secret in os.environ
    if not api_key_present:
        raise ValueError(f"{api_key_secret} is not set in the environment")
    client = OpenAI(base_url=base_url, api_key=os.environ[api_key_secret])
    if schema:
        text_format = pydantic_model_from_schema_dict(schema)
        messages = [messages] if isinstance(messages, dict) else messages
        response = client.responses.parse(
            text_format=text_format, model=model, input=messages, stream=False
        )
        response = {
            "response": response.model_dump(),
            "parsed_output": response.output_parsed.model_dump(),
        }
    else:
        messages = [messages] if isinstance(messages, dict) else messages
        kwargs = {}
        if enable_image_generation:
            kwargs["tools"] = [{"type": "image_generation"}]
        response = client.responses.create(
            model=model, input=messages, stream=False, **kwargs
        )
        if enable_image_generation:
            image = Image.open(
                BytesIO(
                    base64.b64decode(
                        [
                            output.result
                            for output in response.output
                            if output.type == "image_generation_call"
                        ][0]
                    )
                )
            )
            response = {
                "response": response.model_dump(),
                "image": image,
            }
        else:
            response = response.model_dump()
    return response


def create_litellm_response(
    model: str, messages: list[dict[str, Any]]
) -> dict[str, Any | dict[str, Any]]:
    """
    Create a LiteLLM response.

    Args:
        model: The model to use
        messages: The messages to send to the model
    """
    import rich
    from litellm import completion

    rich.print(messages)
    response = completion(
        model=model,
        messages=messages,
        stream=False,
    ).model_dump()
    return response

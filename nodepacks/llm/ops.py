from typing import Any, Dict, List, Literal

import rich


def LLM_Message(
    role: Literal["user", "assistant", "system", "developer"],
    content: list[dict[str, Any]],
) -> dict[str, Any | dict[str, Any]]:
    rich.print(content)
    return {
        "role": role,
        "content": content,
    }


def create_openai_reponse(
    model: str, messages: str | list[dict[str, Any]], schema: dict | None = None
) -> Any:
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
    from pydantic import BaseModel, create_model

    def json_schema_type_to_py_type(schema: dict) -> Any:
        """Very small JSON-schema → Python type mapper."""
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
    api_key_present = "OPENAI_API_KEY" in os.environ
    if not api_key_present:
        raise ValueError("OPENAI_API_KEY is not set in the environment")
    client = OpenAI()
    if schema:
        text_format = pydantic_model_from_schema_dict(schema)
        messages = [messages] if isinstance(messages, dict) else messages
        rich.print("[bold green]Creating response with schema...[/bold green]")
        rich.print(text_format.model_json_schema())
        rich.print(messages)
        response = client.responses.parse(
            text_format=text_format, model=model, input=messages, stream=False
        )
        response = {
            "response": response.model_dump(),
            "parsed_output": response.output_parsed.model_dump(),
        }
    else:
        messages = [messages] if isinstance(messages, dict) else messages
        response = client.responses.create(
            model=model, input=messages, stream=False
        ).model_dump()
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

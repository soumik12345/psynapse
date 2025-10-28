"""Node schemas for the backend."""

from typing import Any, Dict, List

# Define node schemas
NODE_SCHEMAS = [
    {
        "name": "add",
        "params": [
            {"name": "a", "type": "float"},
            {"name": "b", "type": "float"},
        ],
        "returns": [
            {"name": "result", "type": "float"},
        ],
    },
    {
        "name": "subtract",
        "params": [
            {"name": "a", "type": "float"},
            {"name": "b", "type": "float"},
        ],
        "returns": [
            {"name": "result", "type": "float"},
        ],
    },
    {
        "name": "multiply",
        "params": [
            {"name": "a", "type": "float"},
            {"name": "b", "type": "float"},
        ],
        "returns": [
            {"name": "result", "type": "float"},
        ],
    },
    {
        "name": "divide",
        "params": [
            {"name": "a", "type": "float"},
            {"name": "b", "type": "float"},
        ],
        "returns": [
            {"name": "result", "type": "float"},
        ],
    },
    {
        "name": "view",
        "params": [
            {"name": "value", "type": "any"},
        ],
        "returns": [],
    },
]


def get_node_schemas() -> List[Dict[str, Any]]:
    """Get all node schemas."""
    return NODE_SCHEMAS


def get_node_schema(name: str) -> Dict[str, Any]:
    """Get a specific node schema by name."""
    for schema in NODE_SCHEMAS:
        if schema["name"] == name:
            return schema
    return None

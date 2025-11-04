"""Node schemas for the backend."""

import os
from glob import glob
from typing import Any, Dict, List

from psynapse.utils import (
    generate_node_schema_from_python_function,
    get_functions_from_file,
)


def populate_node_schemas() -> List[Dict[str, Any]]:
    """Populate the node schemas from the nodepacks directory."""
    node_schemas = []
    print(os.getcwd())
    for filepath in glob(os.path.join(os.getcwd(), "nodepacks", "*.py")):
        functions = get_functions_from_file(filepath)
        for func in functions:
            node_schema = generate_node_schema_from_python_function(func)
            node_schema["filepath"] = filepath
            node_schemas.append(node_schema)
    return node_schemas


def get_node_schemas() -> List[Dict[str, Any]]:
    """Get all node schemas."""
    return populate_node_schemas()


def get_node_schema(name: str) -> Dict[str, Any]:
    """Get a specific node schema by name."""
    for schema in populate_node_schemas():
        if schema["name"] == name:
            return schema
    return None

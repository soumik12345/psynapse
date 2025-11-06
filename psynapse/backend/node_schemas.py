"""Node schemas for the backend."""

from pathlib import Path
from typing import Any, Dict, List

from psynapse.utils import (
    generate_node_schema_from_python_function,
    get_functions_from_file,
)

# Cache for node schemas to avoid repeated file scanning
_SCHEMA_CACHE: List[Dict[str, Any]] = []


def _get_project_root() -> Path:
    """Get the project root directory by finding the directory containing pyproject.toml."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    # Fallback to current working directory
    return Path.cwd()


def populate_node_schemas() -> List[Dict[str, Any]]:
    """Populate the node schemas from the nodepacks directory."""
    global _SCHEMA_CACHE

    # Return cached schemas if already populated
    if _SCHEMA_CACHE:
        return _SCHEMA_CACHE

    node_schemas = []
    project_root = _get_project_root()
    nodepacks_dir = project_root / "nodepacks"

    if not nodepacks_dir.exists():
        # Try current working directory as fallback
        nodepacks_dir = Path.cwd() / "nodepacks"

    if nodepacks_dir.exists():
        # Iterate through subdirectories in nodepacks
        for nodepack_dir in nodepacks_dir.iterdir():
            # Skip non-directories and special directories like __pycache__
            if not nodepack_dir.is_dir() or nodepack_dir.name.startswith("__"):
                continue

            # Look for ops.py in each nodepack directory
            ops_file = nodepack_dir / "ops.py"
            if ops_file.exists():
                functions = get_functions_from_file(str(ops_file))
                for func in functions:
                    node_schema = generate_node_schema_from_python_function(func)
                    node_schema["filepath"] = str(ops_file)
                    node_schemas.append(node_schema)

    _SCHEMA_CACHE = node_schemas
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

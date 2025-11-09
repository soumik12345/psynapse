import ast
import inspect
import json
import sys
from typing import Any, Dict, List, get_args, get_origin, get_type_hints

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

# Import Literal based on Python version
if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


def pretty_print_payload(payload: dict, title: str):
    """Pretty print a payload to the console."""
    console = Console()
    console.print(
        Panel(
            Syntax(json.dumps(payload, indent=4), "json"),
            title=title,
        )
    )


def type_to_string(type_hint) -> str:
    """Convert a type hint to a string representation."""
    # Handle basic types
    if type_hint == int:
        return "int"
    elif type_hint == float:
        return "float"
    elif type_hint == str:
        return "str"
    elif type_hint == bool:
        return "bool"
    elif type_hint == list or type_hint == List:
        return "list"
    elif type_hint == dict or type_hint == Dict:
        return "dict"
    # Check for Literal types
    elif get_origin(type_hint) is Literal:
        return "str"  # Literal types are still strings, but we'll handle options separately
    elif hasattr(type_hint, "__name__"):
        return type_hint.__name__
    else:
        # Fallback to string representation
        return str(type_hint).replace("typing.", "").lower()


def extract_literal_values(type_hint) -> List[str] | None:
    """Extract values from a Literal type hint.

    Args:
        type_hint: A type hint that may be a Literal

    Returns:
        List of literal values if the type is Literal, None otherwise
    """
    if get_origin(type_hint) is Literal:
        return list(get_args(type_hint))
    return None


def generate_node_schema_from_python_function(func: callable) -> Dict[str, Any]:
    """Generate a node schema from a Python callable.

    Args:
        func: A callable with type hints for all parameters and return type.

    Returns:
        A dictionary representing the node schema in the format:
        {
            "name": str,
            "params": [{"name": str, "type": str, "options": List[str] (optional)}, ...],
            "returns": [{"name": str, "type": str}, ...],
            "docstring": str (optional)
        }
    """
    # Get function name
    name = func.__name__

    # Get type hints
    type_hints = get_type_hints(func)

    # Get function signature
    sig = inspect.signature(func)

    # Get docstring
    docstring = inspect.getdoc(func)

    # Build params list
    params = []
    for param_name, param in sig.parameters.items():
        if param_name in type_hints:
            type_hint = type_hints[param_name]
            # Convert type to string representation
            type_str = type_to_string(type_hint)
            param_dict = {"name": param_name, "type": type_str}

            # Check if this is a Literal type and extract options
            literal_values = extract_literal_values(type_hint)
            if literal_values:
                param_dict["options"] = literal_values

            params.append(param_dict)

    # Build returns list
    returns = []
    if "return" in type_hints:
        return_type = type_hints["return"]
        type_str = type_to_string(return_type)
        returns.append({"name": "result", "type": type_str})

    schema = {
        "name": name,
        "params": params,
        "returns": returns,
    }

    # Add docstring if available
    if docstring:
        schema["docstring"] = docstring

    return schema


def get_functions_from_file(filepath: str) -> list[callable]:
    """
    Get a list of function objects defined in a Python file.

    Args:
        filepath: Path to the Python file

    Returns:
        List of function objects found in the file
    """
    import importlib.util
    import sys

    # Load the module from the file path
    spec = importlib.util.spec_from_file_location("nodepack_module", filepath)
    if spec is None or spec.loader is None:
        return []

    module = importlib.util.module_from_spec(spec)
    sys.modules["nodepack_module"] = module
    spec.loader.exec_module(module)

    # Parse the file to get function names
    with open(filepath, "r") as f:
        file_content = f.read()

    tree = ast.parse(file_content)

    # Extract function names
    function_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            function_names.append(node.name)

    # Get the actual function objects from the module
    functions = []
    for func_name in function_names:
        if hasattr(module, func_name):
            func = getattr(module, func_name)
            if callable(func):
                functions.append(func)

    return functions

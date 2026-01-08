import importlib.util
import inspect
from pathlib import Path
from typing import Any, Literal, get_args, get_origin, get_type_hints


def get_type_name(type_hint: Any) -> str:
    """
    Convert a type hint to a string representation.

    Args:
        type_hint: The type hint to convert.

    Returns:
        A string representation of the type hint.
    """
    if type_hint is None or type_hint is type(None):
        return "None"

    # Handle basic types
    if type_hint == int:
        return "int"
    elif type_hint == float:
        return "float"
    elif type_hint == str:
        return "str"
    elif type_hint == bool:
        return "bool"
    elif hasattr(type_hint, "__name__"):
        return type_hint.__name__
    else:
        return str(type_hint)


def get_literal_values(type_hint: Any) -> list[str] | None:
    """
    Extract literal values from a Literal type hint.

    Args:
        type_hint: The type hint to check.

    Returns:
        A list of string values if the type hint is Literal, None otherwise.
    """
    try:
        origin = get_origin(type_hint)
        if origin is Literal:
            # Get the literal values and convert them to strings
            args = get_args(type_hint)
            return [str(arg) for arg in args]
    except Exception:
        pass
    return None


def extract_function_schema(func: callable, filepath: str) -> dict[str, Any]:
    """
    Extract schema information from a function.

    Args:
        func: The function to extract schema information from.
        filepath: The file path of the function.

    Returns:
        A dictionary of schema information.
    """
    try:
        # Get function signature
        sig = inspect.signature(func)

        # Get type hints
        type_hints = get_type_hints(func)

        # Extract parameters
        params = []
        for param_name, param in sig.parameters.items():
            param_type = type_hints.get(param_name, Any)
            param_info = {"name": param_name, "type": get_type_name(param_type)}

            # Add default value if it exists
            if param.default is not inspect.Parameter.empty:
                param_info["default"] = param.default

            # Check for Literal type and extract values
            literal_values = get_literal_values(param_type)
            if literal_values:
                param_info["literal_values"] = literal_values

            params.append(param_info)

        # Extract return type
        return_type = type_hints.get("return", Any)
        returns = [{"name": "result", "type": get_type_name(return_type)}]

        # Extract docstring
        docstring = inspect.getdoc(func) or ""

        return {
            "name": func.__name__,
            "params": params,
            "returns": returns,
            "docstring": docstring,
            "filepath": filepath,
        }
    except Exception as e:
        print(f"Error extracting schema for {func.__name__}: {e}")
        return None


def extract_class_schema(cls: type, filepath: str) -> dict[str, Any]:
    """
    Extract schema information from a class with __call__ method.

    Args:
        cls: The class to extract schema information from.
        filepath: The file path of the class.

    Returns:
        A dictionary of schema information.
    """
    try:
        # Get __call__ method signature
        call_method = cls.__call__
        sig = inspect.signature(call_method)

        # Get type hints from __call__ method
        type_hints = get_type_hints(call_method)

        # Extract parameters (skip 'self' parameter)
        params = []
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            param_type = type_hints.get(param_name, Any)
            param_info = {"name": param_name, "type": get_type_name(param_type)}

            # Add default value if it exists
            if param.default is not inspect.Parameter.empty:
                param_info["default"] = param.default

            # Check for Literal type and extract values
            literal_values = get_literal_values(param_type)
            if literal_values:
                param_info["literal_values"] = literal_values

            params.append(param_info)

        # Extract return type
        return_type = type_hints.get("return", Any)
        returns = [{"name": "result", "type": get_type_name(return_type)}]

        # Extract docstring (prefer class docstring, fallback to __call__ docstring)
        docstring = inspect.getdoc(cls) or inspect.getdoc(call_method) or ""

        return {
            "name": cls.__name__,
            "params": params,
            "returns": returns,
            "docstring": docstring,
            "filepath": filepath,
            "is_progress_node": True,
        }
    except Exception as e:
        print(f"Error extracting schema for {cls.__name__}: {e}")
        return None


def extract_schemas_from_file(
    filepath: str, extract_classes: bool = False
) -> list[dict[str, Any]]:
    """
    Extract schemas from all functions or classes in a Python file.

    Args:
        filepath: The file path of the Python file.
        extract_classes: If True, extract classes with __call__ method. If False, extract functions.

    Returns:
        A list of dictionaries of schema information.
    """
    schemas = []

    try:
        # Load the module
        spec = importlib.util.spec_from_file_location("module", filepath)
        if spec is None or spec.loader is None:
            return schemas

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Inspect all members in the module
        for name, obj in inspect.getmembers(module):
            if extract_classes:
                # Extract classes with __call__ method
                if (
                    inspect.isclass(obj)
                    and obj.__module__ == module.__name__
                    and hasattr(obj, "__call__")
                    and not name.startswith("_")  # Skip private classes
                ):
                    schema = extract_class_schema(obj, filepath)
                    if schema:
                        schemas.append(schema)
            else:
                # Extract functions
                if inspect.isfunction(obj) and obj.__module__ == module.__name__:
                    schema = extract_function_schema(obj, filepath)
                    if schema:
                        schemas.append(schema)

    except Exception as e:
        print(f"Error loading module from {filepath}: {e}")

    return schemas


def extract_all_schemas(nodepacks_dir: str) -> list[dict[str, Any]]:
    """
    Extract schemas from all ops.py and progress_ops.py files in the nodepacks directory.

    Args:
        nodepacks_dir: The directory containing the nodepacks.

    Returns:
        A list of dictionaries of schema information.
    """
    all_schemas = []
    nodepacks_path = Path(nodepacks_dir)

    if not nodepacks_path.exists():
        print(f"Nodepacks directory not found: {nodepacks_dir}")
        return all_schemas

    # Iterate through all subdirectories
    for nodepack_dir in nodepacks_path.iterdir():
        if nodepack_dir.is_dir():
            # Extract schemas from regular ops.py functions
            ops_file = nodepack_dir / "ops.py"
            if ops_file.exists():
                schemas = extract_schemas_from_file(
                    str(ops_file), extract_classes=False
                )
                all_schemas.extend(schemas)

            # Extract schemas from progress_ops.py classes
            progress_ops_file = nodepack_dir / "progress_ops.py"
            if progress_ops_file.exists():
                schemas = extract_schemas_from_file(
                    str(progress_ops_file), extract_classes=True
                )
                all_schemas.extend(schemas)

    return all_schemas

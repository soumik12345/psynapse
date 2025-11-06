from typing import Any


def add(a: float, b: float) -> float:
    return a + b


def subtract(a: float, b: float) -> float:
    return a - b


def multiply(a: float, b: float) -> float:
    return a * b


def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Division by zero")
    return a / b


def modulo(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Division by zero")
    return a % b


def power(a: float, b: float) -> float:
    return a**b


def sqrt(a: float) -> float:
    return a**0.5


def log(a: float) -> float:
    import math

    return math.log(a)


def exp(a: float) -> float:
    import math

    return math.exp(a)


def at_index(
    object: list | dict, index: Any
) -> list | dict | None | str | int | float | bool:
    if isinstance(object, list) and not isinstance(index, int):
        raise ValueError("Index for a list must be an integer")
    return object[index]


def query_with_index(obj: list | dict, query: str) -> Any:
    """
    Query a nested list or dict using bracket notation.

    Args:
        obj: The list or dict to query
        query: A string query in bracket notation, e.g., "['output'][0]['content'][0]['text']"

    Returns:
        The value at the specified path

    Example:
        >>> data = {'output': [1, 2, 3]}
        >>> query_with_index(data, "['output'][0]")
        1
    """
    import re

    # Parse the query string to extract indices using bracket notation
    # Pattern matches ['key'] or ["key"] or [0] style indexing
    pattern = r"\[(['\"]?)([^'\"]+?)\1\]"
    matches = re.findall(pattern, query)

    result = obj
    for quote, index in matches:
        if quote:  # String key (quoted)
            result = result[index]
        else:  # Numeric index (unquoted)
            result = result[int(index)]

    return result

import math
from typing import Any


def add(a: float, b: float) -> float:
    """
    Add two numbers.

    Args:
        a: The number to add
        b: The number to add

    Returns:
        The sum of the two numbers
    """
    return a + b


def subtract(a: float, b: float) -> float:
    """
    Subtract two numbers.

    Args:
        a: The number to subtract
        b: The number to subtract by

    Returns:
        The difference of the two numbers
    """
    return a - b


def multiply(a: float, b: float) -> float:
    """
    Multiply two numbers.

    Args:
        a: The number to multiply
        b: The number to multiply by

    Returns:
        The product of the two numbers
    """
    return a * b


def divide(a: float, b: float) -> float:
    """
    Divide two numbers.

    Args:
        a: The number to divide
        b: The number to divide by

    Returns:
        The quotient of the two numbers
    """
    if b == 0:
        raise ValueError("Division by zero")
    return a / b


def modulo(a: float, b: float) -> float:
    """
    Calculate the modulo of two numbers.

    Args:
        a: The number to calculate the modulo of
        b: The number to calculate the modulo of

    Returns:
        The modulo of the two numbers
    """
    if b == 0:
        raise ValueError("Division by zero")
    return a % b


def power(a: float, b: float) -> float:
    return a**b


def sqrt(a: float) -> float:
    """
    Calculate the square root of a number.

    Args:
        a: The number to calculate the square root of

    Returns:
        The square root of the number
    """
    return a**0.5


def log(a: float) -> float:
    """
    Calculate the natural logarithm of a number.

    Args:
        a: The number to calculate the natural logarithm of

    Returns:
        The natural logarithm of the number
    """
    return math.log(a)


def exp(a: float) -> float:
    """
    Exponentiate a number.

    Args:
        a: The number to exponentiate

    Returns:
        The exponentiated number
    """
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


def sum_numbers(numbers: list) -> float:
    """
    Sum a list of numbers.

    Args:
        numbers: A list of numbers to sum

    Returns:
        The sum of all numbers in the list
    """
    # Ensure we received a list
    if not isinstance(numbers, list):
        raise TypeError(f"Expected list, got {type(numbers)}: {numbers}")

    # Convert to floats if needed
    numeric_values = []
    for num in numbers:
        if isinstance(num, str):
            try:
                numeric_values.append(float(num))
            except (ValueError, TypeError):
                numeric_values.append(0)
        else:
            numeric_values.append(float(num) if num is not None else 0)
    return sum(numeric_values)

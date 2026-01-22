import math
from typing import Literal

from psynapse_backend.schema_extractor import AnnotatedDict


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


def greet(name: str, greeting: str = "Hello", punctuation: str = "!") -> str:
    """
    Generate a greeting message with customizable greeting and punctuation.

    This function demonstrates default parameters in the Psynapse workflow editor.
    The 'greeting' and 'punctuation' parameters have defaults and will only appear
    in the node properties panel, not in the node itself.

    Args:
        name: The name of the person to greet (required)
        greeting: The greeting word to use (default: "Hello")
        punctuation: The punctuation to use at the end (default: "!")

    Returns:
        A formatted greeting message
    """
    return f"{greeting}, {name}{punctuation}"


def at_index(object: list | dict, index: int | str) -> any:
    """
    Get the value at a given index from a list or dictionary.

    Args:
        object: The list or dictionary to get the value from
        index: The index to get the value from

    Returns:
        The value at the given index
    """
    if isinstance(object, list):
        return object[int(index)]
    return object[index]


def split_name(full_name: str) -> AnnotatedDict[Literal["first", "last"]]:
    """
    Split a full name into first and last name components.

    This function demonstrates the AnnotatedDict feature which creates
    multiple output handles for the node - one for 'first' and one for 'last'.

    Args:
        full_name: The full name to split (e.g., "John Doe")

    Returns:
        A dictionary with 'first' and 'last' keys containing the name parts
    """
    parts = full_name.strip().split(" ", 1)
    return {
        "first": parts[0],
        "last": parts[1] if len(parts) > 1 else "",
    }


def divmod_numbers(
    a: float, b: float
) -> AnnotatedDict[Literal["quotient", "remainder"]]:
    """
    Calculate both the quotient and remainder of a division operation.

    This function demonstrates the AnnotatedDict feature for mathematical operations,
    creating separate output handles for 'quotient' and 'remainder'.

    Args:
        a: The dividend (number to be divided)
        b: The divisor (number to divide by)

    Returns:
        A dictionary with 'quotient' and 'remainder' keys
    """
    if b == 0:
        raise ValueError("Division by zero")
    return {
        "quotient": a // b,
        "remainder": a % b,
    }

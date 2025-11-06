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

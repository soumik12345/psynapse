# AnnotatedDict: Multiple Output Handles

`AnnotatedDict` is a special return type annotation that allows nodepack functions to have multiple output handles. Instead of a single "output" socket, nodes can expose individual dictionary keys as separate output connections.

## Basic Usage

Import `AnnotatedDict` from the schema extractor and use it with `Literal` to specify output keys:

```python
from typing import Literal
from psynapse_backend.schema_extractor import AnnotatedDict

def split_name(full_name: str) -> AnnotatedDict[Literal["first", "last"]]:
    """Split a full name into first and last name."""
    parts = full_name.strip().split(" ", 1)
    return {
        "first": parts[0],
        "last": parts[1] if len(parts) > 1 else "",
    }
```

This creates a node with two output handles: `first` and `last`. Downstream nodes can connect to either output independently.

## How It Works

1. **Schema Extraction**: When the backend loads your nodepack, it detects the `AnnotatedDict[Literal[...]]` return type and extracts the key names
2. **Frontend Rendering**: The node displays multiple output handles on the right side, one for each key
3. **Execution**: When the node executes, it returns a dictionary. The executor routes each key's value to the appropriate connected edges

## Example: Mathematical Operations

```python
def divmod_numbers(a: float, b: float) -> AnnotatedDict[Literal["quotient", "remainder"]]:
    """Calculate both quotient and remainder of a division."""
    if b == 0:
        raise ValueError("Division by zero")
    return {
        "quotient": a // b,
        "remainder": a % b,
    }
```

## Validation

The executor validates that the returned dictionary contains all expected keys. If a key is missing, a `ValueError` is raised:

```
ValueError: AnnotatedDict output missing expected key 'first'. Available keys: ['name']
```

## Connecting to Downstream Nodes

When connecting an `AnnotatedDict` node to another node:

- Each output handle corresponds to a specific dictionary key
- The connected downstream node receives only the value for that key (not the full dictionary)
- Multiple downstream nodes can connect to different outputs from the same source node

## Comparison with Regular Dict

| Feature | `dict` return | `AnnotatedDict` return |
|---------|---------------|------------------------|
| Output handles | Single "output" | One per specified key |
| Value passed | Full dictionary | Individual key values |
| Schema | `returns: [{name: "result", type: "dict"}]` | `returns: [{name: "key1"}, {name: "key2"}, ...]` |

## Best Practices

1. **Use descriptive key names**: Keys become handle labels in the UI
2. **Keep key count reasonable**: Too many outputs can clutter the node
3. **Document the keys**: Include key descriptions in your docstring
4. **Always return all keys**: The executor validates that all declared keys are present

## Limitations

- Only top-level dictionary keys are supported (no nested access like `user.name`)
- Keys must be string literals defined at annotation time
- The function must return a plain dictionary (not a custom dict subclass)

# Schema Extractor

The Schema Extractor dynamically discovers and extracts metadata from Python functions and classes in nodepacks.

## Features

- **Function Discovery**: Extracts schemas from functions in `ops.py` files
- **Progress Class Discovery**: Extracts schemas from classes with `__call__` methods in `progress_ops.py` files
- **Type Hint Parsing**: Extracts type information from function signatures and annotations
- **Docstring Extraction**: Captures documentation strings for nodes

## Progress Node Support

The schema extractor scans `progress_ops.py` files for classes that:
- Have a `__call__` method
- Are not private (don't start with `_`)
- Are defined at module level

Progress node schemas include an `is_progress_node: true` flag to distinguish them from regular function nodes.

See the [Progress Nodes Guide](../guides/progress-nodes.md) for details on creating progress nodes.

## API Reference

::: psynapse_backend.schema_extractor
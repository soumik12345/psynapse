# Progress Nodes Guide

## Overview

Progress nodes are a special type of node in Psynapse that can report real-time progress updates during execution. These nodes are ideal for long-running operations where users need visual feedback about the execution status.

Progress nodes are implemented as Python classes with a `__call__` method, stored in `progress_ops.py` files within nodepacks. During execution, they report progress updates that are displayed as progress bars in the Status Panel.

## Creating Progress Nodes

### File Structure

Progress nodes must be placed in a `progress_ops.py` file within a nodepack directory:

```
nodepacks/
  └── basic/
      ├── ops.py              # Regular function nodes
      └── progress_ops.py     # Progress-aware nodes
```

### Class Structure

A progress node is a Python class that:

1. Has a `__call__` method that serves as the entry point
2. Contains a `_ProgressReporter` instance for reporting progress
3. Calls `update()` or `update_percent()` during execution

### Example: Basic Progress Node

```python
import time
from typing import Callable, Optional


class _ProgressReporter:
    """Context-aware progress reporter for node execution."""

    def __init__(self):
        self._callback: Optional[Callable[[float, str], None]] = None

    def set_callback(self, callback: Callable[[float, str], None]):
        """Set the callback for progress updates."""
        self._callback = callback

    def update(self, current: int, total: int, message: str = ""):
        """Report progress using current/total."""
        if self._callback:
            progress = current / total if total > 0 else 0
            self._callback(progress, message)

    def update_percent(self, percent: float, message: str = ""):
        """Report progress as percentage (0.0 to 1.0)."""
        if self._callback:
            self._callback(percent, message)


class ProcessItems:
    """Process a list of items with progress reporting."""
    
    def __init__(self):
        self._progress_reporter = _ProgressReporter()

    def __call__(self, count: int) -> int:
        """
        Process items with progress reporting.
        
        Args:
            count: Number of items to process
            
        Returns:
            Sum of processed items
        """
        results = []
        for i in range(count):
            # Simulate work
            time.sleep(0.5)
            results.append(i * 2)
            
            # Report progress
            self._progress_reporter.update(
                i + 1, 
                count, 
                f"Processing item {i + 1}/{count}"
            )
        
        return sum(results)
```

### Key Components

#### 1. `_ProgressReporter` Class

The `_ProgressReporter` class handles progress callbacks:

- **`set_callback(callback)`**: Sets the callback function (called by executor)
- **`update(current, total, message)`**: Reports progress using current/total ratio
- **`update_percent(percent, message)`**: Reports progress as a percentage (0.0-1.0)

#### 2. Progress Node Class

Your progress node class must:

- **Have `__init__`**: Create a `_ProgressReporter` instance
- **Have `__call__`**: Implement the main logic with progress reporting
- **Call `update()` or `update_percent()`**: Report progress during execution

### Progress Reporting Methods

#### Using `update(current, total, message)`

```python
def __call__(self, items: list) -> list:
    results = []
    total = len(items)
    
    for i, item in enumerate(items):
        # Process item
        result = process(item)
        results.append(result)
        
        # Report progress: automatically calculates percentage
        self._progress_reporter.update(
            i + 1,           # Current item number
            total,           # Total items
            f"Processing {item}"  # Optional message
        )
    
    return results
```

#### Using `update_percent(percent, message)`

```python
def __call__(self, steps: int) -> float:
    result = 0.0
    
    for i in range(steps):
        # Perform calculation
        result += calculate_step(i)
        
        # Report progress: manually calculate percentage
        percent = (i + 1) / steps
        self._progress_reporter.update_percent(
            percent,
            f"Step {i + 1}/{steps}"
        )
    
    return result
```

## Execution Flow

When a progress node is executed:

1. **Discovery**: Schema extractor finds the class in `progress_ops.py`
2. **Registration**: Class is registered in `progress_class_registry`
3. **Instantiation**: Executor creates a new instance of the class
4. **Callback Setup**: Executor sets the progress callback on `_progress_reporter`
5. **Thread Execution**: `__call__` method runs in a separate thread
6. **Progress Streaming**: Progress updates are streamed via Server-Sent Events
7. **UI Update**: Status Panel displays progress bar with percentage

## Frontend Display

Progress nodes display in the Status Panel with:

- **Progress Bar**: Visual indicator showing completion percentage
- **Progress Message**: Custom message from the node
- **Percentage Text**: Numeric percentage display
- **Spinner**: Animated indicator showing active execution

The progress bar updates in real-time as the node reports progress.

## Best Practices

### 1. Report Progress Frequently

Report progress at regular intervals, especially for long-running operations:

```python
# Good: Report every iteration
for i, item in enumerate(items):
    process(item)
    self._progress_reporter.update(i + 1, len(items))

# Bad: Report only at the end
for item in items:
    process(item)
self._progress_reporter.update(len(items), len(items))  # Too late!
```

### 2. Use Descriptive Messages

Provide meaningful progress messages:

```python
# Good
self._progress_reporter.update(
    i + 1, 
    total, 
    f"Processing file: {filename}"
)

# Bad
self._progress_reporter.update(i + 1, total, "")
```

### 3. Handle Errors Gracefully

Ensure progress reporting doesn't break error handling:

```python
def __call__(self, items: list) -> list:
    results = []
    try:
        for i, item in enumerate(items):
            result = process(item)
            results.append(result)
            self._progress_reporter.update(i + 1, len(items))
    except Exception as e:
        # Error will be caught by executor
        raise
    return results
```

### 4. Consider Performance

Progress reporting has minimal overhead, but avoid excessive updates:

```python
# Good: Report every N items for large datasets
for i, item in enumerate(items):
    process(item)
    if i % 100 == 0 or i == len(items) - 1:
        self._progress_reporter.update(i + 1, len(items))

# Also fine: Report every item for smaller datasets
for i, item in enumerate(items):
    process(item)
    self._progress_reporter.update(i + 1, len(items))
```

## Advanced Examples

### Example: File Processing with Nested Progress

```python
class ProcessFiles:
    def __init__(self):
        self._progress_reporter = _ProgressReporter()

    def __call__(self, files: list[str]) -> dict:
        results = {}
        total_files = len(files)
        
        for file_idx, filename in enumerate(files):
            # Report file-level progress
            self._progress_reporter.update(
                file_idx + 1,
                total_files,
                f"Processing file: {filename}"
            )
            
            # Process file with line-level progress
            file_results = []
            lines = read_file(filename)
            for line_idx, line in enumerate(lines):
                processed = process_line(line)
                file_results.append(processed)
                
                # Report line-level progress
                self._progress_reporter.update_percent(
                    (file_idx + (line_idx + 1) / len(lines)) / total_files,
                    f"File {file_idx + 1}/{total_files}: Line {line_idx + 1}/{len(lines)}"
                )
            
            results[filename] = file_results
        
        return results
```

### Example: Iterative Algorithm with Progress

```python
class IterativeSolver:
    def __init__(self):
        self._progress_reporter = _ProgressReporter()

    def __call__(self, iterations: int, tolerance: float) -> float:
        value = 0.0
        
        for i in range(iterations):
            # Perform iteration
            value = iterate(value)
            
            # Check convergence
            if abs(value - previous_value) < tolerance:
                self._progress_reporter.update_percent(
                    1.0,
                    f"Converged after {i + 1} iterations"
                )
                break
            
            # Report progress
            self._progress_reporter.update(
                i + 1,
                iterations,
                f"Iteration {i + 1}: value = {value:.6f}"
            )
        
        return value
```

## Troubleshooting

### Progress Bar Not Appearing

- Ensure your class has `__call__` method
- Verify `_progress_reporter` is created in `__init__`
- Check that `update()` or `update_percent()` is called during execution
- Ensure the class is in `progress_ops.py` (not `ops.py`)

### Progress Updates Not Showing

- Check that progress is reported frequently enough
- Verify the executor is using streaming mode (`/execute/stream`)
- Check browser console for SSE connection errors

### Class Not Discovered

- Ensure class name doesn't start with `_` (private classes are skipped)
- Verify file is named `progress_ops.py` exactly
- Check that class is defined at module level (not nested)
- Restart backend after adding new progress nodes

## API Reference

### `_ProgressReporter` Methods

#### `update(current: int, total: int, message: str = "")`

Report progress using current item and total items.

- **current**: Current item number (1-indexed)
- **total**: Total number of items
- **message**: Optional progress message

#### `update_percent(percent: float, message: str = "")`

Report progress as a percentage.

- **percent**: Progress percentage (0.0 to 1.0)
- **message**: Optional progress message

### Schema Format

Progress nodes are included in the schema with `is_progress_node: true`:

```json
{
  "name": "ProcessItems",
  "params": [
    {"name": "count", "type": "int"}
  ],
  "returns": [
    {"name": "result", "type": "int"}
  ],
  "docstring": "Process items with progress reporting.",
  "filepath": "/path/to/progress_ops.py",
  "is_progress_node": true
}
```

## See Also

- [Architecture Guide](architecture.md) - System architecture overview
- [Graph Executor](../backend/executor.md) - Execution details
- [Schema Extractor](../backend/schema_extractor.md) - Schema extraction process


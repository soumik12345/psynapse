# Graph Executor

The Graph Executor is responsible for executing node graphs in the correct order with dependency resolution.

## Features

- **Topological Sorting**: Uses Kahn's algorithm to determine execution order
- **Function Execution**: Executes regular Python functions from `ops.py`
- **Progress Node Execution**: Executes progress-aware classes from `progress_ops.py` with real-time progress reporting
- **Streaming Execution**: Provides real-time status updates via Server-Sent Events
- **Error Handling**: Gracefully handles execution errors and reports them

## Progress Node Support

Progress nodes are classes with `__call__` methods that can report progress during execution. The executor:

1. Detects progress nodes by checking the `progress_class_registry`
2. Instantiates the class
3. Sets up a progress callback on the `_progress_reporter` attribute
4. Executes the `__call__` method in a separate thread
5. Streams progress updates via SSE during execution

See the [Progress Nodes Guide](../guides/progress-nodes.md) for details on creating progress nodes.

## API Reference

::: psynapse_backend.executor

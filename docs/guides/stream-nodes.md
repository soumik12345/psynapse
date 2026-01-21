# Stream Nodes Guide

## Overview

Stream nodes are a special type of node in Psynapse that can emit text chunks in real-time during execution. These nodes are ideal for operations that produce incremental text output, such as LLM token streaming, where users want to see the response as it's being generated.

Stream nodes are implemented as Python classes with a `__call__` method, stored in `stream_ops.py` files within nodepacks. During execution, they emit text chunks that are displayed in real-time in the Status Panel.

## Creating Stream Nodes

### File Structure

Stream nodes must be placed in a `stream_ops.py` file within a nodepack directory:

```
nodepacks/
  └── my_nodepack/
      ├── ops.py              # Regular function nodes
      ├── progress_ops.py     # Progress-aware nodes
      └── stream_ops.py       # Streaming text nodes
```

### Class Structure

A stream node is a Python class that:

1. Has a `__call__` method that serves as the entry point
2. Contains a `_StreamReporter` instance for emitting text chunks
3. Calls `emit()` during execution to stream text

### Example: Basic Stream Node

```python
from typing import Callable, Optional


class _StreamReporter:
    """Context-aware stream reporter for streaming text content."""

    def __init__(self):
        self._callback: Optional[Callable[[str], None]] = None

    def set_callback(self, callback: Callable[[str], None]):
        """Set the callback for stream updates."""
        self._callback = callback

    def emit(self, chunk: str):
        """Emit a text chunk to the stream."""
        if self._callback and chunk:
            self._callback(chunk)


class StreamText:
    """Stream text word by word."""

    def __init__(self):
        self._stream_reporter = _StreamReporter()

    def __call__(self, text: str, delay: float = 0.1) -> str:
        """
        Stream text content word by word.

        Args:
            text: The text to stream
            delay: Delay between words in seconds

        Returns:
            The complete text
        """
        import time

        words = text.split()
        for i, word in enumerate(words):
            time.sleep(delay)
            # Add space after word (except for last word)
            chunk = word + (" " if i < len(words) - 1 else "")
            self._stream_reporter.emit(chunk)

        return text
```

### Key Components

#### 1. `_StreamReporter` Class

The `_StreamReporter` class handles streaming callbacks:

- **`set_callback(callback)`**: Sets the callback function (called by executor)
- **`emit(chunk)`**: Emits a text chunk to be displayed in real-time

#### 2. Stream Node Class

Your stream node class must:

- **Have `__init__`**: Create a `_StreamReporter` instance
- **Have `__call__`**: Implement the main logic with stream emission
- **Call `emit()`**: Emit text chunks during execution

### Streaming Method

#### Using `emit(chunk)`

```python
def __call__(self, prompt: str) -> str:
    response_parts = []

    for token in generate_tokens(prompt):
        # Emit token immediately for real-time display
        self._stream_reporter.emit(token)
        response_parts.append(token)

    # Return the complete response
    return "".join(response_parts)
```

## Execution Flow

When a stream node is executed:

1. **Discovery**: Schema extractor finds the class in `stream_ops.py`
2. **Registration**: Class is registered in `stream_class_registry`
3. **Instantiation**: Executor creates a new instance of the class
4. **Callback Setup**: Executor sets the stream callback on `_stream_reporter`
5. **Thread Execution**: `__call__` method runs in a separate thread
6. **Chunk Streaming**: Text chunks are streamed via Server-Sent Events (SSE)
7. **UI Update**: Status Panel displays accumulated text in real-time

## Frontend Display

Stream nodes display in the Status Panel with:

- **Streaming Text**: Accumulated text shown as it arrives
- **Real-time Updates**: Each chunk appends to the display immediately
- **Spinner**: Animated indicator showing active streaming
- **Final Result**: Complete output shown when streaming completes

The text updates in real-time as the node emits chunks, providing immediate feedback.

## Best Practices

### 1. Emit Meaningful Chunks

Emit chunks at natural boundaries (tokens, words, sentences):

```python
# Good: Emit complete tokens/words
for token in tokenize(text):
    self._stream_reporter.emit(token)

# Bad: Emit individual characters (too granular)
for char in text:
    self._stream_reporter.emit(char)
```

### 2. Handle Empty Chunks

The `_StreamReporter.emit()` method ignores empty chunks, but it's good practice to check:

```python
# Good: The reporter handles this, but explicit checks are clearer
for chunk in generate_chunks():
    if chunk:
        self._stream_reporter.emit(chunk)
```

### 3. Return Complete Output

Always return the complete output from `__call__`, not just the last chunk:

```python
def __call__(self, input_text: str) -> str:
    accumulated = []

    for chunk in process(input_text):
        self._stream_reporter.emit(chunk)
        accumulated.append(chunk)

    # Return the complete result
    return "".join(accumulated)
```

### 4. Handle Errors Gracefully

Ensure streaming doesn't break error handling:

```python
def __call__(self, prompt: str) -> str:
    accumulated = []
    try:
        for chunk in generate_response(prompt):
            self._stream_reporter.emit(chunk)
            accumulated.append(chunk)
    except Exception as e:
        # Error will be caught by executor
        raise
    return "".join(accumulated)
```

### 5. Consider Chunk Size

For optimal UX, balance chunk size with update frequency:

```python
# Good: Natural chunk sizes (tokens, words)
for token in llm_stream:
    self._stream_reporter.emit(token)

# Good: Buffered output for very fast streams
buffer = []
for char in fast_stream:
    buffer.append(char)
    if len(buffer) >= 10 or char in '.!?\n':
        self._stream_reporter.emit("".join(buffer))
        buffer = []
```

## Advanced Examples

### Example: LLM Chat Completion Streaming

```python
import os
from typing import Any, Callable, Literal, Optional


class _StreamReporter:
    """Context-aware stream reporter for streaming text content."""

    def __init__(self):
        self._callback: Optional[Callable[[str], None]] = None

    def set_callback(self, callback: Callable[[str], None]):
        """Set the callback for stream updates."""
        self._callback = callback

    def emit(self, chunk: str):
        """Emit a text chunk to the stream."""
        if self._callback and chunk:
            self._callback(chunk)


class OpenAIChatCompletionStream:
    """
    Make a streaming chat completion request to OpenAI.

    This node streams tokens in real-time to the Execution Status panel,
    allowing you to see the response as it's being generated.
    """

    def __init__(self):
        self._stream_reporter = _StreamReporter()

    def __call__(
        self,
        model: str,
        messages: list[dict[str, str]],
        api_key_variable: str = "OPENAI_API_KEY",
        temperature: float | None = None,
    ) -> dict[str, Any]:
        """
        Make a streaming chat completion request.

        Args:
            model: The model to use (e.g., "gpt-4")
            messages: The conversation messages
            api_key_variable: Environment variable containing API key
            temperature: Sampling temperature (0-2)

        Returns:
            Complete response dict with message content
        """
        from openai import OpenAI

        api_key = os.getenv(api_key_variable)
        if not api_key:
            raise ValueError(f"Environment variable '{api_key_variable}' not set")

        client = OpenAI(api_key=api_key)

        # Make streaming request
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=temperature,
        )

        # Accumulate and stream the response
        accumulated_content = []

        for chunk in stream:
            if chunk.choices:
                for choice in chunk.choices:
                    if choice.delta and choice.delta.content:
                        content = choice.delta.content
                        accumulated_content.append(content)
                        # Emit chunk for real-time display
                        self._stream_reporter.emit(content)

        full_content = "".join(accumulated_content)

        return {
            "model": model,
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": full_content,
                }
            }]
        }
```

### Example: File Reader with Streaming Output

```python
class StreamFileContents:
    """Stream file contents line by line."""

    def __init__(self):
        self._stream_reporter = _StreamReporter()

    def __call__(self, filepath: str) -> str:
        """
        Read and stream file contents line by line.

        Args:
            filepath: Path to the file to read

        Returns:
            Complete file contents
        """
        lines = []

        with open(filepath, 'r') as f:
            for line in f:
                self._stream_reporter.emit(line)
                lines.append(line)

        return "".join(lines)
```

### Example: Text Transformation with Streaming

```python
class StreamTransform:
    """Transform text and stream the result."""

    def __init__(self):
        self._stream_reporter = _StreamReporter()

    def __call__(self, text: str, transform: str = "uppercase") -> str:
        """
        Transform text and stream the output.

        Args:
            text: Input text to transform
            transform: Transformation type (uppercase, lowercase, title)

        Returns:
            Transformed text
        """
        import time

        # Split into sentences for natural streaming
        sentences = text.replace('. ', '.|').split('|')
        result_parts = []

        for sentence in sentences:
            # Apply transformation
            if transform == "uppercase":
                transformed = sentence.upper()
            elif transform == "lowercase":
                transformed = sentence.lower()
            else:
                transformed = sentence.title()

            # Stream the transformed sentence
            self._stream_reporter.emit(transformed)
            result_parts.append(transformed)

            # Small delay for visual effect
            time.sleep(0.1)

        return "".join(result_parts)
```

## Stream Nodes vs Progress Nodes

| Feature | Stream Nodes | Progress Nodes |
|---------|--------------|----------------|
| **Purpose** | Emit incremental text output | Report completion percentage |
| **File** | `stream_ops.py` | `progress_ops.py` |
| **Reporter** | `_StreamReporter` | `_ProgressReporter` |
| **Method** | `emit(chunk)` | `update(current, total, message)` |
| **UI Display** | Accumulated text | Progress bar with percentage |
| **Use Case** | LLM streaming, text generation | File processing, batch operations |

Choose stream nodes when you want to show text as it's generated. Choose progress nodes when you want to show completion status of a multi-step operation.

## Troubleshooting

### Streaming Text Not Appearing

- Ensure your class has a `__call__` method
- Verify `_stream_reporter` is created in `__init__`
- Check that `emit()` is called with non-empty strings
- Ensure the class is in `stream_ops.py` (not `ops.py`)

### Chunks Not Displaying in Real-Time

- Verify the executor is using streaming mode (`/execute/stream`)
- Check that chunks are emitted during processing, not all at once at the end
- Check browser console for SSE connection errors

### Class Not Discovered

- Ensure class name doesn't start with `_` (private classes are skipped)
- Verify file is named `stream_ops.py` exactly
- Check that class is defined at module level (not nested)
- Restart backend after adding new stream nodes

### Output Not Matching Streamed Text

- Ensure `__call__` returns the complete accumulated text
- Verify all emitted chunks are also added to the return value

## API Reference

### `_StreamReporter` Methods

#### `emit(chunk: str)`

Emit a text chunk to the stream.

- **chunk**: Text chunk to emit (empty strings are ignored)

### Schema Format

Stream nodes are included in the schema with `is_stream_node: true`:

```json
{
  "name": "StreamText",
  "params": [
    {"name": "text", "type": "str"},
    {"name": "delay", "type": "float", "default": 0.1}
  ],
  "returns": [
    {"name": "result", "type": "str"}
  ],
  "docstring": "Stream text word by word.",
  "filepath": "/path/to/stream_ops.py",
  "is_stream_node": true
}
```

### SSE Event Format

Stream updates are sent via Server-Sent Events with this structure:

```json
{
  "node_id": "node-123",
  "status": "streaming",
  "streaming_text": "Hello world so far...",
  "streaming_chunk": "so far..."
}
```

- **streaming_text**: The accumulated text received so far
- **streaming_chunk**: The latest chunk that was emitted

## See Also

- [Progress Nodes Guide](progress-nodes.md) - Progress reporting nodes
- [Architecture Guide](architecture.md) - System architecture overview


# Psynapse

A python-native node-based UI editor.

## Features

- **Visual Node Editor**: Intuitive drag-and-drop interface for creating node graphs
- **Decoupled Execution**: FastAPI backend handles graph execution separately from the UI
- **Built-in Nodes**: Includes Object, Add, Subtract, Multiply, Divide, and View nodes
- **Typed Input Nodes**: Object node with dynamic widgets for different data types (int, float, string, bool)
- **Error Handling**: Comprehensive error handling with persistent toast notifications
- **On-Demand Execution**: Execute graphs when you're ready with the Run button
- **Interactive Canvas**: Pan, zoom, and navigate your node graph with ease

<figure class="video_container">
  <video controls="true" allowfullscreen="true">
    <source src="assets/demo.mp4" type="video/mp4">
  </video>
</figure>

## Installation

```bash
uv pip install -U git+https://github.com/soumik12345/psynapse.git
```

## Usage

### Quick Start

Simply run the command `psynapse` in the terminal, this would launch the Psynapse application with a locally hosted execution runtime.

### Run with a remote backend

1. Start the execution runtime locally or in a remote VM using

    ```bash
    psynapse-backend
    ```

    The backend will be available at `http://localhost:8000`.

2. Launch the Psynapse editor using

    ```bash
    psynapse
    ```

## Acknowledgments

Inspired by [Nodezator](https://github.com/IndiePython/nodezator), a powerful node editor for Python.

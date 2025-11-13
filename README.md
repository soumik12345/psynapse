# Psynapse

A cross-platform node-based UI editor for building AI workflows using Python.

https://github.com/user-attachments/assets/e75dd546-75d0-4594-a838-def97513d27e

## Features

Psynapse provides a simple and intuitive interface to build and deploy AI workflows using Python using a an intuitive node-based editor. The biggest strength of Psynapse lies in the following 2 aspects:

1. Its written entirely in Python, making it easy to extend, customize and integrate with other Python libraries.
2. Developing your own nodepacks for AI libraries in the Python ecosystem is as easy as writing a simple Python function with type hints for parameters and return values.
3. The decoupled execution runtime allows you to run your workflows on a remote server or GPU clusters, while running the editor on your local machine.

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
    psynapse-backend --port 8000
    ```

    The backend will be available at `http://localhost:8000`.

2. Launch the Psynapse editor using

    ```bash
    psynapse --backend-port 8000
    ```


## Sample Workflows

- [OpenAI Workflows](https://geekyrakshit.dev/psynapse/sample-workflows/openai-workflows/)
- [LiteLLM Workflows](https://geekyrakshit.dev/psynapse/sample-workflows/litellm-workflows/)

## Acknowledgments

Psynapse is heavily inspired by [Nodezator](https://github.com/IndiePython/nodezator) and [ComfyUI](https://github.com/comfyanonymous/ComfyUI).

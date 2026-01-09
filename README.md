# Psynapse

A visual node-based workflow editor for creating and executing computational graphs with Python. Psynapse is meant to be the single no-code workflow editor that lets you harness the entire power of the python ecosystem using simple nodepacks and intuitive drag-and-drop interface.

https://github.com/user-attachments/assets/309ea22a-1fdc-4685-baf5-cd728441c329

## Features

- **Visual Node Editor**: Drag-and-drop interface built with ReactFlow
- **Python Backend**: FastAPI server with real-time execution streaming
- **Extensible Nodepacks**: Add custom Python functions as nodes
- **Type-Safe**: Full TypeScript frontend and type-hinted Python backend
- **Progress Tracking**: Real-time progress updates for long-running operations
- **Multiple Node Types**: Functions, variables, lists, and view nodes

## Quick Start

### Using Docker Compose (Recommended)

```bash
docker compose -f docker/docker-compose.yml up --build
```

For LLM nodepacks, use:

```bash
OPTIONAL_DEPS=llm docker compose -f docker/docker-compose.yml up --build
```

Access the editor at `http://localhost:5173`

### Local Development

**Backend:**
```bash
uv sync
psynapse-backend run --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Architecture

- **Backend** ([psynapse_backend](psynapse_backend/)): FastAPI server with graph execution engine
- **Frontend** ([frontend](frontend/)): React 19 + TypeScript + Vite
- **Nodepacks** ([nodepacks](nodepacks/)): Extensible Python function libraries

## Creating Custom Nodepacks

Add a new directory in `nodepacks/` with an `ops.py` file:

```python
def my_function(text: str, count: int = 1) -> str:
    """Repeats text multiple times."""
    return text * count
```

Restart the backend to auto-register your nodes.

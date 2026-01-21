import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import typer
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from psynapse_backend.executor import GraphExecutor
from psynapse_backend.schema_extractor import extract_all_schemas


def _make_json_serializable(obj: Any, seen: set | None = None) -> Any:
    """
    Recursively convert an object to a JSON-serializable form.
    Non-serializable objects are converted to their repr() string.

    Args:
        obj: The object to convert.
        seen: Set of object ids already processed (for circular reference detection).

    Returns:
        A JSON-serializable version of the object.
    """
    if seen is None:
        seen = set()

    # Handle None
    if obj is None:
        return None

    # Handle primitives (these are always JSON-serializable)
    if isinstance(obj, (bool, int, float, str)):
        return obj

    # Check for circular references
    obj_id = id(obj)
    if obj_id in seen:
        return f"<circular reference: {type(obj).__name__}>"
    seen.add(obj_id)

    try:
        # Handle lists
        if isinstance(obj, list):
            return [_make_json_serializable(item, seen) for item in obj]

        # Handle tuples (convert to list for JSON)
        if isinstance(obj, tuple):
            return [_make_json_serializable(item, seen) for item in obj]

        # Handle dicts
        if isinstance(obj, dict):
            return {str(k): _make_json_serializable(v, seen) for k, v in obj.items()}

        # Try to serialize as-is first
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            pass

        # For objects with __dict__, try to convert to dict
        if hasattr(obj, "__dict__") and not isinstance(obj, type):
            try:
                return {
                    "__repr__": repr(obj),
                    "__type__": type(obj).__name__,
                }
            except Exception:
                pass

        # Fallback: use repr()
        return repr(obj)

    except Exception:
        # Ultimate fallback
        try:
            return repr(obj)
        except Exception:
            return f"<unserializable: {type(obj).__name__}>"
    finally:
        seen.discard(obj_id)


# Get nodepacks directory path - will be set at startup
NODEPACKS_DIR = os.getenv(
    "NODEPACKS_DIR", str(Path(__file__).parent.parent / "nodepacks")
)

# Initialize graph executor - will be set at startup
graph_executor = None


def set_nodepacks_dir(nodepack_dir: str):
    """
    Set the nodepacks directory and initialize the graph executor.
    """
    global NODEPACKS_DIR, graph_executor
    NODEPACKS_DIR = nodepack_dir
    graph_executor = GraphExecutor(NODEPACKS_DIR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler to initialize the graph executor on startup.
    """
    global graph_executor
    if graph_executor is None:
        set_nodepacks_dir(NODEPACKS_DIR)
    yield
    # Cleanup code can go here if needed


app = FastAPI(title="Psynapse Backend", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExecuteRequest(BaseModel):
    """
    Request body for executing a node graph.

    Attributes:
        nodes: The nodes of the graph.
        edges: The edges of the graph.``
        env_vars: Optional environment variables to set during execution.
    """

    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    env_vars: dict[str, str] | None = None


@app.get("/")
def read_root():
    return {"message": "Psynapse Backend API"}


@app.get("/get_schema")
def get_schema():
    """
    Extract and return schemas for all functions in nodepacks.
    """
    try:
        schemas = extract_all_schemas(NODEPACKS_DIR)
        return schemas
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error extracting schemas: {str(e)}"
        )


@app.post("/execute")
def execute_graph(request: ExecuteRequest):
    """
    Execute a node graph and return ViewNode results.
    """
    try:
        results = graph_executor.execute_graph(
            request.nodes, request.edges, request.env_vars
        )
        serializable_results = _make_json_serializable(results)
        return {"results": serializable_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing graph: {str(e)}")


@app.post("/execute/stream")
def execute_graph_stream(request: ExecuteRequest):
    """
    Execute a node graph and stream execution status updates via Server-Sent Events.
    """

    def event_generator():
        try:
            for status_update in graph_executor.execute_graph_streaming(
                request.nodes, request.edges, request.env_vars
            ):
                serializable_update = _make_json_serializable(status_update)
                yield f"data: {json.dumps(serializable_update)}\n\n"
        except Exception as e:
            error_event = {
                "status": "error",
                "error": str(e),
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


# Typer CLI
cli = typer.Typer(help="Psynapse Backend CLI")


@cli.command()
def run(
    host: str = typer.Option("0.0.0.0", help="Host to bind the server to"),
    port: int = typer.Option(8000, help="Port to bind the server to"),
    reload: bool = typer.Option(False, help="Enable auto-reload for development"),
    nodepack_dir: str = typer.Option(
        str(Path(__file__).parent.parent / "nodepacks"),
        help="Directory containing nodepacks",
    ),
):
    """
    Start the Psynapse backend server.
    """
    import uvicorn

    # Set the nodepacks directory before starting the server
    set_nodepacks_dir(nodepack_dir)

    uvicorn.run(
        "psynapse_backend.main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    cli()

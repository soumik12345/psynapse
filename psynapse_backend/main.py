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
        edges: The edges of the graph.
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
        return {"results": results}
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
                # Format as SSE event
                yield f"data: {json.dumps(status_update)}\n\n"
        except Exception as e:
            # Send error event
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

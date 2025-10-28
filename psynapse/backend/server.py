"""FastAPI server for Psynapse backend."""

from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from psynapse.backend.executor import GraphExecutor
from psynapse.backend.node_schemas import get_node_schemas
from psynapse.utils import pretty_print_payload

app = FastAPI(title="Psynapse Backend", version="0.1.0")

# Add CORS middleware to allow requests from the PySide6 frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GraphData(BaseModel):
    """Graph data structure for execution."""

    nodes: list[Dict[str, Any]]
    edges: list[Dict[str, Any]]


@app.get("/nodes")
async def get_nodes():
    """Get all available node schemas.

    Returns:
        List of node schemas with their parameters and return values
    """
    return {"nodes": get_node_schemas()}


@app.post("/execute")
async def execute_graph(graph_data: GraphData):
    """Execute a node graph and return results.

    Args:
        graph_data: Graph structure with nodes and edges

    Returns:
        Dictionary mapping ViewNode IDs to their computed values
    """
    pretty_print_payload(graph_data.model_dump(), "Received Graph Payload on Backend")

    try:
        executor = GraphExecutor(graph_data.model_dump())
        results = executor.execute()

        pretty_print_payload(results, "Execution Results")

        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

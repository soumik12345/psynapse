"""FastAPI server for Psynapse backend."""

import asyncio
import logging
import queue
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("psynapse.backend")

# Queue for log messages to be streamed via SSE
log_queue = queue.Queue()


class QueueHandler(logging.Handler):
    """Custom logging handler that puts messages into a queue."""

    def emit(self, record):
        try:
            msg = self.format(record)
            log_queue.put(msg)
        except Exception:
            self.handleError(record)


# Add queue handler to logger
queue_handler = QueueHandler()
queue_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(queue_handler)

# Also add handler to uvicorn logger
uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.addHandler(queue_handler)


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
    logger.info("Fetching node schemas")
    schemas = get_node_schemas()
    logger.info(f"Returning {len(schemas)} node schemas")
    return {"nodes": schemas}


@app.post("/execute")
async def execute_graph(graph_data: GraphData):
    """Execute a node graph and return results.

    Args:
        graph_data: Graph structure with nodes and edges

    Returns:
        Dictionary mapping ViewNode IDs to their computed values
    """
    logger.info(
        f"Executing graph with {len(graph_data.nodes)} nodes and {len(graph_data.edges)} edges"
    )
    pretty_print_payload(graph_data.model_dump(), "Received Graph Payload on Backend")

    try:
        executor = GraphExecutor(graph_data.model_dump())
        results = executor.execute()

        pretty_print_payload(results, "Execution Results")
        logger.info("Graph execution completed successfully")

        return {"results": results}
    except Exception as e:
        logger.error(f"Graph execution failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.debug("Health check requested")
    return {"status": "ok"}


@app.get("/logs")
async def stream_logs():
    """Stream backend logs via Server-Sent Events.

    Returns:
        EventSourceResponse that streams log messages as they occur
    """

    async def event_generator():
        """Generate SSE events from log queue."""
        logger.info("Log streaming client connected")
        try:
            while True:
                # Check queue for new messages
                try:
                    # Non-blocking get with short timeout
                    msg = log_queue.get(timeout=0.1)
                    yield {"event": "log", "data": msg}
                except queue.Empty:
                    # Send keepalive comment to keep connection open
                    await asyncio.sleep(0.1)
                    continue
        except asyncio.CancelledError:
            logger.info("Log streaming client disconnected")
            raise

    return EventSourceResponse(event_generator())

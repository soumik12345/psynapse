"""FastAPI server for Psynapse backend."""

import asyncio
import json
import logging
import queue
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from psynapse.backend.executor import GraphExecutor, get_current_node
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


class AccessLogFilter(logging.Filter):
    """Filter to suppress access logs for specific endpoints."""

    def filter(self, record):
        """Filter out access logs for /logs and /current_node endpoints."""
        # Check if this is an access log message
        message = record.getMessage()
        # Suppress logs for /logs and /current_node endpoints
        if "/logs" in message or "/current_node" in message:
            return False
        return True


# Apply filter to uvicorn.access logger to suppress access logs for specific endpoints
uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.addFilter(AccessLogFilter())


class GraphData(BaseModel):
    """Graph data structure for execution."""

    nodes: list[Dict[str, Any]]
    edges: list[Dict[str, Any]]


class ExecutionRequest(BaseModel):
    """Execution request with graph and environment variables."""

    graph: GraphData
    env_vars: Dict[str, str] = {}


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
async def execute_graph(request: ExecutionRequest):
    """Execute a node graph and return results.

    Args:
        request: Execution request with graph data and environment variables

    Returns:
        Dictionary mapping ViewNode IDs to their computed values
    """
    logger.info(
        f"Executing graph with {len(request.graph.nodes)} nodes and {len(request.graph.edges)} edges"
    )
    if request.env_vars:
        logger.info(f"Using {len(request.env_vars)} environment variables")
    pretty_print_payload(
        request.graph.model_dump(), "Received Graph Payload on Backend"
    )

    try:
        executor = GraphExecutor(request.graph.model_dump(), request.env_vars)
        results = executor.execute()

        pretty_print_payload(results, "Execution Results")
        logger.info("Graph execution completed successfully")

        return {"results": results}
    except Exception as e:
        logger.error(f"Graph execution failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/execute-stream")
async def execute_graph_stream(request: ExecutionRequest):
    """Execute a node graph and stream progress updates via SSE.

    Args:
        request: Execution request with graph data and environment variables

    Returns:
        EventSourceResponse that streams progress updates and final results
    """
    logger.info(
        f"Executing graph with streaming for {len(request.graph.nodes)} nodes and {len(request.graph.edges)} edges"
    )
    if request.env_vars:
        logger.info(f"Using {len(request.env_vars)} environment variables")
    pretty_print_payload(
        request.graph.model_dump(), "Received Graph Payload on Backend (Streaming)"
    )

    async def event_generator():
        """Generate SSE events from executor progress updates."""
        try:
            # Execute in a thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            executor = GraphExecutor(request.graph.model_dump(), request.env_vars)

            # Run the generator in a separate thread
            def run_executor():
                """Run executor and return all progress updates."""
                updates = []
                try:
                    for update in executor.execute_with_progress():
                        updates.append(update)
                    return updates
                except Exception as e:
                    logger.error(f"Graph execution failed: {str(e)}")
                    return [{"event": "error", "error": str(e), "results": {}}]

            # Execute in thread pool
            updates = await loop.run_in_executor(None, run_executor)

            # Yield all updates as SSE events
            for update in updates:
                event_type = update.get("event", "progress")
                yield {"event": event_type, "data": json.dumps(update)}

            logger.info("Graph execution stream completed successfully")

        except asyncio.CancelledError:
            logger.info("Execution stream client disconnected")
            raise
        except Exception as e:
            logger.error(f"Stream error: {str(e)}")
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.debug("Health check requested")
    return {"status": "ok"}


@app.get("/current_node")
async def current_node():
    """Get the currently executing node.

    Returns:
        Dictionary with node_id and node_type, or null if no execution in progress
    """
    node_info = get_current_node()
    return {"current_node": node_info}


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

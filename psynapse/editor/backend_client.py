"""HTTP client for communicating with the Psynapse backend."""

import asyncio
import json
from typing import Any, Callable, Dict

import aiohttp


class BackendClient:
    """Client for communicating with the Psynapse FastAPI backend."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the backend client.

        Args:
            base_url: Base URL of the backend server
        """
        self.base_url = base_url

    async def get_node_schemas(self) -> Dict[str, Any]:
        """Fetch available node schemas from the backend.

        Returns:
            Dictionary containing node schemas
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/nodes") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to fetch node schemas: {response.status}")

    async def execute_graph(
        self, graph_data: Dict[str, Any], env_vars: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Execute a graph on the backend.

        Args:
            graph_data: Serialized graph structure
            env_vars: Optional environment variables to set during execution

        Returns:
            Dictionary with execution results
        """
        # Include env_vars in the request payload
        payload = {"graph": graph_data, "env_vars": env_vars or {}}

        # Set a very long timeout for graph execution (3600 seconds = 1 hour)
        # This supports long-running node operations (e.g., 10-15 minutes or more)
        timeout = aiohttp.ClientTimeout(total=3600)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{self.base_url}/execute", json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(
                        f"Failed to execute graph: {response.status} - {error_text}"
                    )

    async def execute_graph_stream(
        self,
        graph_data: Dict[str, Any],
        env_vars: Dict[str, str] = None,
        progress_callback: Callable[[str, str], None] = None,
    ) -> Dict[str, Any]:
        """Execute a graph on the backend with progress streaming.

        Args:
            graph_data: Serialized graph structure
            env_vars: Optional environment variables to set during execution
            progress_callback: Optional callback(node_id, node_type) called for each node

        Returns:
            Dictionary with execution results
        """
        # Include env_vars in the request payload
        payload = {"graph": graph_data, "env_vars": env_vars or {}}

        # Set a very long timeout for graph execution (3600 seconds = 1 hour)
        timeout = aiohttp.ClientTimeout(total=3600)

        results = None

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{self.base_url}/execute-stream", json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(
                        f"Failed to execute graph: {response.status} - {error_text}"
                    )

                # Process SSE stream with unlimited line size
                # We need to read chunks and split into lines manually to avoid aiohttp's
                # default 8KB line size limit, which is too small for base64 encoded images
                buffer = b""
                async for chunk in response.content.iter_any():
                    buffer += chunk

                    # Process complete lines from buffer
                    while b"\n" in buffer:
                        line_bytes, buffer = buffer.split(b"\n", 1)
                        line = line_bytes.decode("utf-8").strip()

                        if not line or line.startswith(":"):
                            continue

                        # Parse SSE format: "event: type\ndata: json"
                        if line.startswith("event:"):
                            event_type = line.split(":", 1)[1].strip()
                        elif line.startswith("data:"):
                            data_str = line.split(":", 1)[1].strip()
                            try:
                                data = json.loads(data_str)

                                # Handle different event types
                                if data.get("event") == "progress":
                                    node_id = data.get("node_id")
                                    node_type = data.get("node_type")
                                    if progress_callback:
                                        progress_callback(node_id, node_type)

                                elif data.get("event") == "complete":
                                    results = data.get("results", {})

                                elif data.get("event") == "error":
                                    error_msg = data.get("error", "Unknown error")
                                    results = data.get("results", {})
                                    # Still return results, they will contain error info
                                    break

                            except json.JSONDecodeError:
                                continue

        if results is None:
            raise Exception("No results received from backend")

        return {"results": results}

    async def health_check(self) -> bool:
        """Check if the backend is healthy.

        Returns:
            True if backend is reachable and healthy
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/health", timeout=aiohttp.ClientTimeout(total=2)
                ) as response:
                    return response.status == 200
        except Exception:
            return False

    def execute_graph_sync(
        self, graph_data: Dict[str, Any], env_vars: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Synchronous wrapper for execute_graph.

        Args:
            graph_data: Serialized graph structure
            env_vars: Optional environment variables to set during execution

        Returns:
            Dictionary with execution results
        """
        return asyncio.run(self.execute_graph(graph_data, env_vars))

    def get_node_schemas_sync(self) -> Dict[str, Any]:
        """Synchronous wrapper for get_node_schemas.

        Returns:
            Dictionary containing node schemas
        """
        return asyncio.run(self.get_node_schemas())

    def health_check_sync(self) -> bool:
        """Synchronous wrapper for health_check.

        Returns:
            True if backend is reachable and healthy
        """
        return asyncio.run(self.health_check())

    async def get_current_node(self) -> Dict[str, Any]:
        """Get the currently executing node.

        Returns:
            Dictionary with current_node info (node_id, node_type) or None
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/current_node",
                    timeout=aiohttp.ClientTimeout(total=1),
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"current_node": None}
        except Exception:
            return {"current_node": None}

    def get_current_node_sync(self) -> Dict[str, Any]:
        """Synchronous wrapper for get_current_node.

        Returns:
            Dictionary with current_node info (node_id, node_type) or None
        """
        return asyncio.run(self.get_current_node())

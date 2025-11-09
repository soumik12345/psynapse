"""HTTP client for communicating with the Psynapse backend."""

import asyncio
from typing import Any, Dict

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

        async with aiohttp.ClientSession() as session:
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

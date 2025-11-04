"""Graph execution engine for the backend."""

import importlib.util
import sys
from collections import deque
from typing import Any, Dict, List

from psynapse.backend.node_schemas import get_node_schema


class GraphExecutor:
    """Executes a node graph and returns results."""

    def __init__(self, graph_data: Dict[str, Any]):
        """Initialize executor with graph data.

        Args:
            graph_data: Dictionary containing:
                - nodes: List of node definitions with id, type, and params
                - edges: List of connections between nodes
        """
        self.nodes = graph_data.get("nodes", [])
        self.edges = graph_data.get("edges", [])
        self.node_cache = {}  # Cache for node execution results
        # Build node lookup map for faster access
        self.node_map = {node["id"]: node for node in self.nodes}

    def execute(self) -> Dict[str, Any]:
        """Execute the graph using topological sort and return results for ViewNodes.

        Returns:
            Dictionary mapping view node IDs to their computed values
        """
        # Clear cache for fresh execution
        self.node_cache = {}

        try:
            # Perform topological sort to get execution order
            sorted_nodes = self._topological_sort()

            # Execute nodes in topologically sorted order
            for node_id in sorted_nodes:
                self._execute_node(node_id)

            # Collect results for view nodes
            results = {}
            view_node_ids = [
                node["id"] for node in self.nodes if node["type"] == "view"
            ]
            for view_node_id in view_node_ids:
                if view_node_id in self.node_cache:
                    results[view_node_id] = {
                        "value": self.node_cache[view_node_id],
                        "error": None,
                    }
                else:
                    results[view_node_id] = {
                        "value": None,
                        "error": "Node not executed",
                    }

            return results

        except Exception as e:
            # If there's an error (like a cycle), return error for all view nodes
            view_node_ids = [
                node["id"] for node in self.nodes if node["type"] == "view"
            ]
            results = {}
            for view_node_id in view_node_ids:
                results[view_node_id] = {"value": None, "error": str(e)}
            return results

    def _topological_sort(self) -> List[str]:
        """Perform topological sort using Kahn's algorithm.

        Returns:
            List of node IDs in topologically sorted order

        Raises:
            ValueError: If the graph contains a cycle
        """
        # Build adjacency list and in-degree count
        adjacency = {node["id"]: [] for node in self.nodes}
        in_degree = {node["id"]: 0 for node in self.nodes}

        # Build the graph structure based on socket connections
        for edge in self.edges:
            # Find source and target nodes
            source_node_id = self._find_node_by_socket(edge["start_socket"], "output")
            target_node_id = self._find_node_by_socket(edge["end_socket"], "input")

            if source_node_id and target_node_id:
                adjacency[source_node_id].append(target_node_id)
                in_degree[target_node_id] += 1

        # Initialize queue with nodes having no dependencies (in-degree = 0)
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        sorted_order = []

        # Process nodes in topological order
        while queue:
            node_id = queue.popleft()
            sorted_order.append(node_id)

            # Reduce in-degree for dependent nodes
            for neighbor in adjacency[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Check if all nodes were processed (no cycle)
        if len(sorted_order) != len(self.nodes):
            raise ValueError(
                "Graph contains a cycle - topological sort is not possible"
            )

        return sorted_order

    def _find_node_by_socket(self, socket_id: str, socket_type: str) -> str:
        """Find the node ID that owns a given socket.

        Args:
            socket_id: ID of the socket
            socket_type: Either 'input' or 'output'

        Returns:
            Node ID or None if not found
        """
        socket_key = "input_sockets" if socket_type == "input" else "output_sockets"

        for node in self.nodes:
            for socket in node.get(socket_key, []):
                if socket["id"] == socket_id:
                    return node["id"]
        return None

    def _execute_node(self, node_id: str) -> Any:
        """Execute a single node and cache its result.

        Args:
            node_id: ID of the node to execute

        Returns:
            Result value from node execution
        """
        # Check cache first
        if node_id in self.node_cache:
            return self.node_cache[node_id]

        # Find node definition
        node = self.node_map.get(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")

        # Special handling for ObjectNode - it has a preset output value
        if node["type"] == "object":
            # ObjectNode has no inputs, just return its output value
            output_sockets = node.get("output_sockets", [])
            if output_sockets and "value" in output_sockets[0]:
                result = output_sockets[0]["value"]
            else:
                result = None
            self.node_cache[node_id] = result
            return result

        # Get input values from already-executed nodes (thanks to topological sort)
        inputs = self._get_node_inputs(node_id)

        # Execute based on node type
        result = self._execute_node_operation(node["type"], inputs)

        # Cache result
        self.node_cache[node_id] = result

        return result

    def _get_node_inputs(self, node_id: str) -> Dict[str, Any]:
        """Get input values for a node from the cache.

        Since we execute in topological order, all dependencies are already computed.

        Args:
            node_id: ID of the node to get inputs for

        Returns:
            Dictionary mapping input parameter names to their values
        """
        node = self.node_map.get(node_id)
        inputs = {}

        # For each input socket of this node
        for socket in node.get("input_sockets", []):
            socket_id = socket["id"]
            param_name = socket["name"]

            # Find edge connected to this input socket
            connected_edge = None
            for edge in self.edges:
                if edge["end_socket"] == socket_id:
                    connected_edge = edge
                    break

            if connected_edge:
                # Find the source node
                source_socket_id = connected_edge["start_socket"]
                source_node_id = self._find_node_by_socket(source_socket_id, "output")

                if source_node_id and source_node_id in self.node_cache:
                    # Get the cached result from the source node
                    inputs[param_name] = self.node_cache[source_node_id]
                else:
                    # No connection or not in cache, use default value from socket
                    inputs[param_name] = socket.get("value")
            else:
                # No connection, use default value from socket
                inputs[param_name] = socket.get("value")

        return inputs

    def _execute_node_operation(self, node_type: str, inputs: Dict[str, Any]) -> Any:
        """Execute a node's operation based on its type.

        Args:
            node_type: Type of node (e.g., add, subtract, multiply, divide, view)
            inputs: Dictionary of input values

        Returns:
            Result of the operation
        """
        # Special handling for view node
        if node_type == "view":
            # View node just passes through its input
            return inputs.get("value")

        # Get the node schema from nodepacks
        schema = get_node_schema(node_type)
        if not schema:
            raise ValueError(f"Unknown node type: {node_type}")

        # Load the function from the nodepack file
        filepath = schema["filepath"]
        spec = importlib.util.spec_from_file_location("nodepack_module", filepath)
        if spec is None or spec.loader is None:
            raise ValueError(f"Could not load module from {filepath}")

        module = importlib.util.module_from_spec(spec)
        sys.modules["nodepack_module"] = module
        spec.loader.exec_module(module)

        # Get the function from the module
        if not hasattr(module, node_type):
            raise ValueError(f"Function {node_type} not found in {filepath}")

        func = getattr(module, node_type)

        # Call the function with the inputs
        return func(**inputs)

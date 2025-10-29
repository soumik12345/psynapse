"""Graph execution engine for the backend."""

from typing import Any, Dict


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

    def execute(self) -> Dict[str, Any]:
        """Execute the graph and return results for ViewNodes.

        Returns:
            Dictionary mapping view node IDs to their computed values
        """
        # Clear cache for fresh execution
        self.node_cache = {}

        # Find all view nodes
        view_node_ids = [node["id"] for node in self.nodes if node["type"] == "view"]

        # Execute each view node and collect results
        results = {}
        for view_node_id in view_node_ids:
            try:
                value = self._execute_node(view_node_id)
                results[view_node_id] = {"value": value, "error": None}
            except Exception as e:
                results[view_node_id] = {"value": None, "error": str(e)}

        return results

    def _execute_node(self, node_id: str) -> Any:
        """Execute a single node and return its result.

        Args:
            node_id: ID of the node to execute

        Returns:
            Result value from node execution
        """
        # Check cache first
        if node_id in self.node_cache:
            return self.node_cache[node_id]

        # Find node definition
        node = self._find_node(node_id)
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

        # Get input values by recursively executing connected nodes
        inputs = self._get_node_inputs(node_id)

        # Execute based on node type
        result = self._execute_node_operation(node["type"], inputs)

        # Cache result
        self.node_cache[node_id] = result

        return result

    def _find_node(self, node_id: str) -> Dict[str, Any]:
        """Find a node by its ID."""
        for node in self.nodes:
            if node["id"] == node_id:
                return node
        return None

    def _get_node_inputs(self, node_id: str) -> Dict[str, Any]:
        """Get input values for a node by tracing back through edges.

        Args:
            node_id: ID of the node to get inputs for

        Returns:
            Dictionary mapping input parameter names to their values
        """
        node = self._find_node(node_id)
        inputs = {}

        # For each input socket of this node
        for i, socket in enumerate(node.get("input_sockets", [])):
            socket_id = socket["id"]
            param_name = socket["name"]

            # Find edge connected to this input socket
            connected_edge = None
            for edge in self.edges:
                if edge["end_socket"] == socket_id:
                    connected_edge = edge
                    break

            if connected_edge:
                # Find the source node and socket
                source_socket_id = connected_edge["start_socket"]
                source_node_id, source_socket_idx = self._find_socket_owner(
                    source_socket_id
                )

                if source_node_id:
                    # Execute source node to get its output value
                    source_result = self._execute_node(source_node_id)
                    inputs[param_name] = source_result
                else:
                    # No connection, use default value from socket
                    inputs[param_name] = socket.get("value")
            else:
                # No connection, use default value from socket
                inputs[param_name] = socket.get("value")

        return inputs

    def _find_socket_owner(self, socket_id: str) -> tuple[str, int]:
        """Find which node owns a socket.

        Returns:
            Tuple of (node_id, socket_index)
        """
        for node in self.nodes:
            for i, socket in enumerate(node.get("output_sockets", [])):
                if socket["id"] == socket_id:
                    return (node["id"], i)
        return (None, None)

    def _execute_node_operation(self, node_type: str, inputs: Dict[str, Any]) -> Any:
        """Execute a node's operation based on its type.

        Args:
            node_type: Type of node (add, subtract, multiply, divide, view)
            inputs: Dictionary of input values

        Returns:
            Result of the operation
        """
        if node_type == "add":
            a = float(inputs.get("a", 0.0))
            b = float(inputs.get("b", 0.0))
            return a + b

        elif node_type == "subtract":
            a = float(inputs.get("a", 0.0))
            b = float(inputs.get("b", 0.0))
            return a - b

        elif node_type == "multiply":
            a = float(inputs.get("a", 1.0))
            b = float(inputs.get("b", 1.0))
            return a * b

        elif node_type == "divide":
            a = float(inputs.get("a", 1.0))
            b = float(inputs.get("b", 1.0))
            if b == 0:
                raise ZeroDivisionError("Division by zero")
            return a / b

        elif node_type == "view":
            # View node just passes through its input
            return inputs.get("value")

        else:
            raise ValueError(f"Unknown node type: {node_type}")

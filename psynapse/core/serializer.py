"""Graph serialization for communication with backend."""

from typing import Any, Dict, List

from psynapse.core.node import Node
from psynapse.nodes.object_node import ObjectNode
from psynapse.nodes.ops import OpNode
from psynapse.nodes.view_node import ViewNode


class GraphSerializer:
    """Serializes a node graph to a format suitable for backend execution."""

    # Map node classes to their backend type names (for non-OpNode nodes)
    NODE_TYPE_MAP = {
        ObjectNode: "object",
        ViewNode: "view",
    }

    @staticmethod
    def serialize_graph(nodes: List[Node]) -> Dict[str, Any]:
        """Serialize a list of nodes into a graph structure.

        Args:
            nodes: List of Node instances from the editor

        Returns:
            Dictionary with 'nodes' and 'edges' keys
        """
        serialized_nodes = []
        serialized_edges = []

        # Build node ID mapping
        node_id_map = {}
        for i, node in enumerate(nodes):
            node_id = f"node_{i}"
            node_id_map[id(node)] = node_id

        # Serialize nodes
        for node in nodes:
            node_id = node_id_map[id(node)]
            node_type = GraphSerializer._get_node_type(node)

            # Serialize input sockets
            input_sockets = []
            for socket in node.input_sockets:
                input_sockets.append(
                    {
                        "id": f"{node_id}_input_{socket.index}",
                        "name": socket.label.lower(),
                        "value": socket.value,
                    }
                )

            # Serialize output sockets
            output_sockets = []
            for socket in node.output_sockets:
                socket_data = {
                    "id": f"{node_id}_output_{socket.index}",
                    "name": socket.label.lower(),
                }
                # Include value for output sockets that have a preset value (e.g., ObjectNode)
                if socket.value is not None:
                    socket_data["value"] = socket.value
                output_sockets.append(socket_data)

            serialized_nodes.append(
                {
                    "id": node_id,
                    "type": node_type,
                    "input_sockets": input_sockets,
                    "output_sockets": output_sockets,
                }
            )

        # Serialize edges
        for node in nodes:
            node_id = node_id_map[id(node)]

            # Check input sockets for connections
            for socket in node.input_sockets:
                for edge in socket.edges:
                    if edge.start_socket and edge.end_socket:
                        start_node_id = node_id_map.get(id(edge.start_socket.node))
                        end_node_id = node_id_map.get(id(edge.end_socket.node))

                        if start_node_id and end_node_id:
                            start_socket_id = (
                                f"{start_node_id}_output_{edge.start_socket.index}"
                            )
                            end_socket_id = (
                                f"{end_node_id}_input_{edge.end_socket.index}"
                            )

                            serialized_edges.append(
                                {
                                    "start_socket": start_socket_id,
                                    "end_socket": end_socket_id,
                                }
                            )

        return {
            "nodes": serialized_nodes,
            "edges": serialized_edges,
        }

    @staticmethod
    def _get_node_type(node: Node) -> str:
        """Get the backend type name for a node.

        Args:
            node: Node instance

        Returns:
            Type name string (e.g., 'add', 'subtract')
        """
        # Check if this is an OpNode (schema-based node)
        if isinstance(node, OpNode):
            return node.node_type

        # Check the NODE_TYPE_MAP for other node types
        for node_class, type_name in GraphSerializer.NODE_TYPE_MAP.items():
            if isinstance(node, node_class):
                return type_name

        # Default fallback
        return "unknown"

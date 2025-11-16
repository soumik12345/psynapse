"""Graph serialization for communication with backend."""

from typing import Any, Dict, List

from psynapse.core.node import Node
from psynapse.nodes.dictionary_node import DictionaryNode
from psynapse.nodes.image_node import ImageNode
from psynapse.nodes.list_node import ListNode
from psynapse.nodes.object_node import ObjectNode
from psynapse.nodes.ops import OpNode
from psynapse.nodes.pydantic_schema_node import PydanticSchemaNode
from psynapse.nodes.text_node import TextNode
from psynapse.nodes.view_node import ViewNode


class GraphSerializer:
    """Serializes a node graph to a format suitable for backend execution."""

    # Map node classes to their backend type names (for non-OpNode nodes)
    # Note: TextNode must come before ObjectNode since TextNode inherits from ObjectNode
    NODE_TYPE_MAP = {
        ImageNode: "image",
        TextNode: "text",
        ObjectNode: "object",
        ViewNode: "view",
        ListNode: "list",
        DictionaryNode: "dictionary",
        PydanticSchemaNode: "pydantic_schema",
    }

    @staticmethod
    def serialize_graph(
        nodes: List[Node], include_output_values: bool = True
    ) -> Dict[str, Any]:
        """Serialize a list of nodes into a graph structure.

        Args:
            nodes: List of Node instances from the editor
            include_output_values: If True, include output socket values in serialization.
                                  If False, exclude output socket values (for saving to file).
                                  Defaults to True for backend execution compatibility.

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
                # Skip PydanticSchemaNode - its value is a type object that can't be serialized
                # The backend will recreate the model from params
                # Only include values if include_output_values is True
                if (
                    include_output_values
                    and socket.value is not None
                    and not isinstance(node, PydanticSchemaNode)
                ):
                    socket_data["value"] = socket.value
                output_sockets.append(socket_data)

            # Get node position (center) and size
            pos = node.graphics.pos()
            center_x = pos.x() + node.graphics.width / 2
            center_y = pos.y() + node.graphics.height / 2
            width = node.graphics.width
            height = node.graphics.height

            node_data = {
                "id": node_id,
                "type": node_type,
                "input_sockets": input_sockets,
                "output_sockets": output_sockets,
                "position": [center_x, center_y],
                "size": [width, height],
            }

            # Include filepath for OpNode instances
            if isinstance(node, OpNode) and hasattr(node, "filepath") and node.filepath:
                node_data["filepath"] = node.filepath

            if (
                isinstance(node, OpNode)
                and hasattr(node, "source_nodepack")
                and node.source_nodepack
            ):
                node_data["source_nodepack"] = node.source_nodepack

            # Include image parameters for ImageNode instances
            if isinstance(node, ImageNode):
                node_data["params"] = {
                    "mode": node.current_mode,
                    "url": node.image_url,
                    "path": node.image_path,
                    "return_as": node.return_as,
                }

            # Include text parameters for TextNode instances
            if isinstance(node, TextNode):
                node_data["params"] = {
                    "return_as": node.return_as,
                }

            # Include schema entries for PydanticSchemaNode instances
            if isinstance(node, PydanticSchemaNode):
                # Serialize entries so backend can recreate the model
                entries = []
                for entry in node.entries:
                    entries.append(
                        {
                            "field": entry["field"],
                            "type": entry["type"],  # Type is already a string
                            "default_value": entry["default_value"],
                        }
                    )
                node_data["params"] = {
                    "entries": entries,
                    "schema_name": node.schema_name,
                }

            serialized_nodes.append(node_data)

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

from pathlib import Path
from typing import Any, Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGraphicsProxyWidget,
    QHBoxLayout,
    QPushButton,
    QWidget,
)

from psynapse.core.node import Node
from psynapse.core.socket import Socket, SocketType
from psynapse.core.socket_types import SocketDataType


class OpNode(Node):
    """Generalized operation node that can be created from a node schema.

    This node is dynamically configured based on the schema received from the backend.
    The actual execution logic is handled by the backend's GraphExecutor, so this node
    only serves as a visual representation in the frontend.
    """

    def __init__(self, schema: Dict[str, Any]):
        """Initialize an OpNode from a schema.

        Args:
            schema: Node schema dictionary containing:
                - name: Node type name (e.g., "add", "subtract")
                - params: List of input parameter definitions
                - returns: List of output definitions
                - filepath: Path to the file containing the node's implementation
                - source_nodepack: Name of the nodepack that contains the node
        """
        self.node_type = schema["name"]
        self.filepath = schema.get("filepath")
        self.source_nodepack = Path(self.filepath).parent.name

        # Track which parameters are list-type (variadic)
        self.variadic_params = {}  # param_name -> {"original_name": str, "base_index": int, "count": int}

        # Convert schema params to input socket specifications
        inputs = []
        for idx, param in enumerate(schema.get("params", [])):
            param_name = param["name"].upper()  # e.g., "a" -> "A"
            param_type_str = param["type"]
            param_type = self._map_type(param_type_str)

            # Track if this is a list-type parameter
            if param_type_str.lower() == "list":
                self.variadic_params[param_name] = {
                    "original_name": param["name"],
                    "base_index": len(inputs),
                    "count": 1,  # Start with one socket
                }
                # For list-type parameters, use indexed name for the first socket
                socket_label = f"{param_name} [0]"
            else:
                socket_label = param_name

            # Check if this parameter has options (for Literal types)
            if "options" in param:
                # Format: (label, type, options, default)
                default_value = param.get("default")
                if default_value is not None:
                    inputs.append(
                        (socket_label, param_type, param["options"], default_value)
                    )
                else:
                    inputs.append((socket_label, param_type, param["options"]))
            else:
                # Check if parameter has a default value
                default_value = param.get("default")
                if default_value is not None:
                    # Format: (label, type, options, default) where options is None
                    inputs.append((socket_label, param_type, None, default_value))
                else:
                    inputs.append((socket_label, param_type))

        # Convert schema returns to output socket specifications
        outputs = []
        for return_spec in schema.get("returns", []):
            return_name = return_spec["name"].capitalize()  # e.g., "result" -> "Result"
            return_type = self._map_type(return_spec["type"])
            outputs.append((return_name, return_type))

        # Initialize with proper title (capitalize the node type name)
        title = schema["name"].replace("_", " ")
        super().__init__(title=title, inputs=inputs, outputs=outputs)

        # Create UI controls for variadic parameters
        self.variadic_button_widgets = {}
        if self.variadic_params:
            self._create_variadic_controls()

    def _map_type(self, type_str: str) -> SocketDataType:
        """Map schema type string to SocketDataType.

        Args:
            type_str: Type string from schema (e.g., "float", "any")

        Returns:
            Corresponding SocketDataType
        """
        type_mapping = {
            "float": SocketDataType.FLOAT,
            "int": SocketDataType.INT,
            "str": SocketDataType.STRING,
            "string": SocketDataType.STRING,
            "bool": SocketDataType.BOOL,
            "any": SocketDataType.ANY,
            "dict": SocketDataType.ANY,  # Dict types map to ANY
        }
        return type_mapping.get(type_str.lower(), SocketDataType.ANY)

    def _create_variadic_controls(self):
        """Create +/- button controls for each variadic parameter."""
        for param_name, param_info in self.variadic_params.items():
            # Create container widget for buttons
            widget_container = QWidget()
            widget_layout = QHBoxLayout()
            widget_layout.setContentsMargins(0, 0, 0, 0)
            widget_layout.setSpacing(8)
            widget_layout.setAlignment(Qt.AlignCenter)
            widget_container.setLayout(widget_layout)

            # Create + button
            add_button = QPushButton("+")
            add_button.setFixedSize(18, 18)
            add_button.clicked.connect(
                lambda checked=False, p=param_name: self._add_variadic_socket(p)
            )
            add_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 9px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)

            # Create - button
            remove_button = QPushButton("−")
            remove_button.setFixedSize(18, 18)
            remove_button.clicked.connect(
                lambda checked=False, p=param_name: self._remove_variadic_socket(p)
            )
            remove_button.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    border-radius: 9px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
                QPushButton:pressed {
                    background-color: #c62828;
                }
            """)

            # Add buttons to layout
            widget_layout.addWidget(add_button)
            widget_layout.addWidget(remove_button)

            # Add widget to graphics
            widget_proxy = QGraphicsProxyWidget(self.graphics)
            widget_proxy.setWidget(widget_container)
            widget_proxy.setZValue(200)

            # Store references
            self.variadic_button_widgets[param_name] = {
                "container": widget_container,
                "proxy": widget_proxy,
                "add_button": add_button,
                "remove_button": remove_button,
            }

        # Update node size and button positions
        self._update_node_size()
        self._update_variadic_button_positions()

    def _update_node_size(self):
        """Update node size based on number of sockets."""
        socket_spacing = 30
        min_height = 100
        calculated_height = 40 + len(self.input_sockets) * socket_spacing + 60
        self.graphics.height = max(min_height, calculated_height)
        self.graphics.setRect(0, 0, self.graphics.width, self.graphics.height)
        self._position_sockets()
        if self.variadic_params:
            self._update_variadic_button_positions()

    def _update_variadic_button_positions(self):
        """Position buttons next to their corresponding variadic parameter sockets."""
        for param_name, param_info in self.variadic_params.items():
            if param_name not in self.variadic_button_widgets:
                continue

            base_index = param_info["base_index"]
            count = param_info["count"]

            # Position buttons at the middle of the variadic sockets
            if count > 0 and base_index < len(self.input_sockets):
                first_socket_y = 40 + base_index * 30
                last_socket_y = 40 + (base_index + count - 1) * 30
                middle_y = (first_socket_y + last_socket_y) / 2

                # Position buttons to the right side of the node
                button_width = 44  # 18 + 8 spacing + 18
                button_x = self.graphics.width - button_width - 10
                button_y = middle_y - 9  # Half of button height (18/2)

                self.variadic_button_widgets[param_name]["proxy"].setPos(
                    button_x, button_y
                )

    def _add_variadic_socket(self, param_name: str):
        """Add a new socket for a variadic parameter."""
        if param_name not in self.variadic_params:
            return

        param_info = self.variadic_params[param_name]
        base_index = param_info["base_index"]
        current_count = param_info["count"]

        # Determine where to insert the new socket
        insert_index = base_index + current_count

        # Get the socket type from the first socket of this parameter
        if base_index < len(self.input_sockets):
            first_socket = self.input_sockets[base_index]
            socket_type = first_socket.data_type
        else:
            socket_type = SocketDataType.ANY

        # Create socket label with index
        socket_label = f"{param_name} [{current_count}]"

        # Create new socket
        socket = Socket(
            self, insert_index, SocketType.INPUT, socket_label, socket_type, None, None
        )

        # Insert into socket list at the correct position
        self.input_sockets.insert(insert_index, socket)

        # Update inputs list for serialization
        self.inputs.insert(insert_index, (socket_label, socket_type))

        # Update indices for all sockets after this one
        for i in range(insert_index + 1, len(self.input_sockets)):
            self.input_sockets[i].index = i

        # Update count in param info
        param_info["count"] += 1

        # Update base indices for parameters that come after this one
        for other_param_name, other_param_info in self.variadic_params.items():
            if other_param_info["base_index"] > base_index:
                other_param_info["base_index"] += 1

        # Update node size and positions
        self._update_node_size()

        # Update all edges
        self.update_edges()

    def _remove_variadic_socket(self, param_name: str):
        """Remove a socket for a variadic parameter."""
        if param_name not in self.variadic_params:
            return

        param_info = self.variadic_params[param_name]

        # Keep at least one socket
        if param_info["count"] <= 1:
            return

        base_index = param_info["base_index"]
        current_count = param_info["count"]

        # Remove the last socket for this parameter
        remove_index = base_index + current_count - 1

        if remove_index >= len(self.input_sockets):
            return

        # Get the socket to remove
        socket_to_remove = self.input_sockets[remove_index]

        # Remove all edges connected to this socket
        edges_to_remove = list(socket_to_remove.edges)
        for edge in edges_to_remove:
            edge.remove()

        # Remove socket graphics from scene
        if socket_to_remove.graphics.scene():
            socket_to_remove.graphics.scene().removeItem(socket_to_remove.graphics)

        # Remove label if it exists
        if socket_to_remove.label_item and socket_to_remove.label_item.scene():
            socket_to_remove.label_item.scene().removeItem(socket_to_remove.label_item)

        # Remove input widget if it exists
        if socket_to_remove.input_proxy and socket_to_remove.input_proxy.scene():
            socket_to_remove.input_proxy.scene().removeItem(
                socket_to_remove.input_proxy
            )

        # Remove from lists
        self.input_sockets.pop(remove_index)
        self.inputs.pop(remove_index)

        # Update indices for all sockets after this one
        for i in range(remove_index, len(self.input_sockets)):
            self.input_sockets[i].index = i

        # Update count in param info
        param_info["count"] -= 1

        # Update base indices for parameters that come after this one
        for other_param_name, other_param_info in self.variadic_params.items():
            if other_param_info["base_index"] > base_index:
                other_param_info["base_index"] -= 1

        # Update node size and positions
        self._update_node_size()

        # Update all edges
        self.update_edges()

    def execute(self) -> Any:
        """No-op execution - actual execution happens on the backend.

        The frontend nodes no longer need to execute operations since the backend's
        GraphExecutor handles all computation. This method exists only to satisfy
        the Node interface.
        """
        # Return None - actual execution is handled by the backend
        return None

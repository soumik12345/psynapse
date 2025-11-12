from pathlib import Path
from typing import Any, Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGraphicsProxyWidget,
    QHBoxLayout,
    QLabel,
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

        # Track which parameters have default values
        self.default_params_indices = []  # List of socket indices that have default values
        self.default_params_values = {}  # Map socket index to default value string from schema
        self.default_params_collapsed = True  # Initially collapsed

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
                inputs.append((socket_label, param_type, param["options"]))
            else:
                inputs.append((socket_label, param_type))

            # Track if this parameter has a default value
            if param.get("has_default", False):
                socket_index = len(inputs) - 1
                self.default_params_indices.append(socket_index)
                # Store the default value string from schema
                if "default" in param:
                    self.default_params_values[socket_index] = param["default"]

        # Convert schema returns to output socket specifications
        outputs = []
        for return_spec in schema.get("returns", []):
            return_name = return_spec["name"].capitalize()  # e.g., "result" -> "Result"
            return_type = self._map_type(return_spec["type"])
            outputs.append((return_name, return_type))

        # Initialize with proper title (capitalize the node type name)
        title = schema["name"].replace("_", " ")
        super().__init__(title=title, inputs=inputs, outputs=outputs)

        # Initialize default params widget early (before variadic controls which may call _update_node_size)
        self.default_params_widget = None

        # Create UI controls for variadic parameters
        self.variadic_button_widgets = {}
        if self.variadic_params:
            self._create_variadic_controls()

        # Create collapsible UI for default parameters
        if self.default_params_indices:
            self._create_default_params_controls()
            self._update_default_params_visibility()

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

    def _create_default_params_controls(self):
        """Create collapsible button for default parameters section."""
        # Create container widget
        widget_container = QWidget()
        widget_layout = QHBoxLayout()
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.setSpacing(5)
        widget_layout.setAlignment(Qt.AlignLeft)
        widget_container.setLayout(widget_layout)

        # Create toggle button
        toggle_button = QPushButton("▶")
        toggle_button.setFixedSize(16, 16)
        toggle_button.clicked.connect(self._toggle_default_params)
        toggle_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                border: none;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #ffffff;
            }
        """)

        # Create label
        label = QLabel("Default Parameters")
        label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 9px;
            }
        """)

        # Add to layout
        widget_layout.addWidget(toggle_button)
        widget_layout.addWidget(label)

        # Add widget to graphics
        widget_proxy = QGraphicsProxyWidget(self.graphics)
        widget_proxy.setWidget(widget_container)
        widget_proxy.setZValue(200)

        # Store references
        self.default_params_widget = {
            "container": widget_container,
            "proxy": widget_proxy,
            "toggle_button": toggle_button,
            "label": label,
        }

        # Position the widget
        self._update_default_params_button_position()

    def _toggle_default_params(self):
        """Toggle visibility of default parameters."""
        self.default_params_collapsed = not self.default_params_collapsed
        self._update_default_params_visibility()
        self._update_default_params_button_position()

    def _parse_default_value(self, default_str: str, data_type: SocketDataType) -> Any:
        """Parse default value string from schema and convert to appropriate type.

        Args:
            default_str: String representation of default value (from repr())
            data_type: The socket data type

        Returns:
            Parsed value of appropriate type
        """
        if not default_str:
            return data_type.get_default_value()

        try:
            # Try to evaluate the repr string (handles strings, numbers, booleans, None)
            # Use ast.literal_eval for safe evaluation
            import ast

            parsed_value = ast.literal_eval(default_str)

            # Convert to appropriate type based on socket data type
            if data_type == SocketDataType.INT:
                return int(parsed_value)
            elif data_type == SocketDataType.FLOAT:
                return float(parsed_value)
            elif data_type == SocketDataType.STRING:
                return str(parsed_value)
            elif data_type == SocketDataType.BOOL:
                return bool(parsed_value)
            else:
                return parsed_value
        except (ValueError, SyntaxError):
            # If parsing fails, try to convert based on type
            if data_type == SocketDataType.STRING:
                # Remove quotes if present
                return default_str.strip("'\"")
            return data_type.get_default_value()

    def _populate_default_value(self, socket: Socket, default_value: Any):
        """Populate socket input widget with default value.

        Args:
            socket: The socket to populate
            default_value: The parsed default value
        """
        if not socket.input_widget:
            return

        # Temporarily disconnect signals to avoid triggering value change handlers
        # during initialization
        from PySide6.QtWidgets import (
            QCheckBox,
            QComboBox,
            QDoubleSpinBox,
            QLineEdit,
            QSpinBox,
        )

        if isinstance(socket.input_widget, QSpinBox):
            socket.input_widget.blockSignals(True)
            socket.input_widget.setValue(int(default_value))
            socket.value = int(default_value)
            socket.input_widget.blockSignals(False)
        elif isinstance(socket.input_widget, QDoubleSpinBox):
            socket.input_widget.blockSignals(True)
            socket.input_widget.setValue(float(default_value))
            socket.value = float(default_value)
            socket.input_widget.blockSignals(False)
        elif isinstance(socket.input_widget, QLineEdit):
            socket.input_widget.blockSignals(True)
            socket.input_widget.setText(str(default_value))
            socket.value = str(default_value)
            socket.input_widget.blockSignals(False)
        elif isinstance(socket.input_widget, QWidget) and socket.input_widget.layout():
            # Checkbox wrapped in container
            checkbox = socket.input_widget.findChild(QCheckBox)
            if checkbox:
                checkbox.blockSignals(True)
                checkbox.setChecked(bool(default_value))
                socket.value = bool(default_value)
                checkbox.blockSignals(False)
        elif isinstance(socket.input_widget, QComboBox):
            socket.input_widget.blockSignals(True)
            # Try to find matching option
            default_str = str(default_value)
            index = socket.input_widget.findText(default_str)
            if index >= 0:
                socket.input_widget.setCurrentIndex(index)
                socket.value = default_str
            socket.input_widget.blockSignals(False)

    def _update_default_params_visibility(self):
        """Update visibility of default parameter sockets."""
        for idx in self.default_params_indices:
            if idx < len(self.input_sockets):
                socket = self.input_sockets[idx]
                # Hide/show socket graphics
                socket.graphics.setVisible(not self.default_params_collapsed)
                # Hide/show label
                if socket.label_item:
                    socket.label_item.setVisible(not self.default_params_collapsed)
                # Hide/show input widget
                if socket.input_proxy:
                    socket.input_proxy.setVisible(not self.default_params_collapsed)

                # If uncollapsing and this is a primitive type, populate with default value
                if (
                    not self.default_params_collapsed
                    and idx in self.default_params_values
                ):
                    # Only populate for primitive types (not list, dict, etc.)
                    if socket.data_type in (
                        SocketDataType.INT,
                        SocketDataType.FLOAT,
                        SocketDataType.STRING,
                        SocketDataType.BOOL,
                    ):
                        default_str = self.default_params_values[idx]
                        parsed_value = self._parse_default_value(
                            default_str, socket.data_type
                        )
                        self._populate_default_value(socket, parsed_value)

        # Update node size and reposition sockets
        self._update_node_size()
        self._position_sockets()

    def _position_sockets(self):
        """Position sockets on the node, skipping hidden default parameter sockets."""
        socket_spacing = 30
        visible_index = 0

        for i, socket in enumerate(self.input_sockets):
            # Skip hidden sockets when positioning
            if i in self.default_params_indices and self.default_params_collapsed:
                continue

            x = 0
            y = 40 + visible_index * socket_spacing
            socket.graphics.setParentItem(self.graphics)
            socket.graphics.setPos(x, y)

            # Position label if it exists
            if socket.label_item:
                socket.label_item.setParentItem(self.graphics)
                label_x = 15
                label_y = y - 8
                socket.label_item.setPos(label_x, label_y)

            # Position input widget if it exists
            if socket.input_widget:
                if not hasattr(socket, "input_proxy") or socket.input_proxy is None:
                    socket.input_proxy = QGraphicsProxyWidget(self.graphics)
                    socket.input_proxy.setWidget(socket.input_widget)
                    socket.input_proxy.setZValue(100 + visible_index)

                widget_x = 15
                if socket.label_item:
                    widget_x = 15 + socket.label_item.boundingRect().width() + 5

                right_margin = 10
                available_width = self.graphics.width - widget_x - right_margin
                min_widget_width = 60
                widget_width = max(min_widget_width, available_width)

                socket.resize_input_widget(widget_width)
                socket.input_proxy.setPos(widget_x, y - 10)

            visible_index += 1

        # Position output sockets normally
        for i, socket in enumerate(self.output_sockets):
            x = self.graphics.width
            y = 40 + i * socket_spacing
            socket.graphics.setParentItem(self.graphics)
            socket.graphics.setPos(x, y)

            if socket.label_item:
                socket.label_item.setParentItem(self.graphics)
                label_width = socket.label_item.boundingRect().width()
                label_x = x - label_width - 15
                label_y = y - 8
                socket.label_item.setPos(label_x, label_y)

    def _update_default_params_button_position(self):
        """Position the default parameters toggle button."""
        if not self.default_params_widget:
            return

        # Count visible sockets (required parameters)
        visible_socket_count = len(self.input_sockets) - len(
            self.default_params_indices
        )
        if not self.default_params_collapsed:
            visible_socket_count = len(self.input_sockets)

        # Position button after the required parameters (or at the start if all are visible)
        socket_spacing = 30
        if self.default_params_collapsed:
            # Position after last required socket
            button_y = 40 + visible_socket_count * socket_spacing + 5
        else:
            # Position at the start of default parameters section
            button_y = 40 + visible_socket_count * socket_spacing + 5

        button_x = 10

        self.default_params_widget["proxy"].setPos(button_x, button_y)

        # Update button icon
        icon = "▼" if not self.default_params_collapsed else "▶"
        self.default_params_widget["toggle_button"].setText(icon)

    def _update_node_size(self):
        """Update node size based on number of visible sockets."""
        socket_spacing = 30
        min_height = 100

        # Count visible sockets
        visible_socket_count = len(self.input_sockets)
        if self.default_params_collapsed:
            visible_socket_count -= len(self.default_params_indices)

        # Add extra space for default params button if there are default params
        extra_height = 0
        if self.default_params_indices:
            extra_height = 25  # Space for the collapsible button

        calculated_height = (
            40 + visible_socket_count * socket_spacing + extra_height + 60
        )
        self.graphics.height = max(min_height, calculated_height)
        self.graphics.setRect(0, 0, self.graphics.width, self.graphics.height)
        self._position_sockets()
        if self.variadic_params:
            self._update_variadic_button_positions()
        if self.default_params_indices:
            self._update_default_params_button_position()

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
            self, insert_index, SocketType.INPUT, socket_label, socket_type, None
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

        # Update default parameter indices and values mapping that come after this insertion
        new_default_params_values = {}
        for i, default_idx in enumerate(self.default_params_indices):
            if default_idx >= insert_index:
                self.default_params_indices[i] += 1
                # Update the values mapping with new index
                if default_idx in self.default_params_values:
                    new_default_params_values[self.default_params_indices[i]] = (
                        self.default_params_values[default_idx]
                    )
            else:
                # Keep old mapping for indices before insertion
                if default_idx in self.default_params_values:
                    new_default_params_values[default_idx] = self.default_params_values[
                        default_idx
                    ]
        self.default_params_values = new_default_params_values

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

        # Update default parameter indices and values mapping that come after this removal
        new_default_params_values = {}
        for i, default_idx in enumerate(self.default_params_indices):
            if default_idx > remove_index:
                self.default_params_indices[i] -= 1
                # Update the values mapping with new index
                if default_idx in self.default_params_values:
                    new_default_params_values[self.default_params_indices[i]] = (
                        self.default_params_values[default_idx]
                    )
            elif default_idx != remove_index:
                # Keep old mapping for indices before removal (skip the removed one)
                if default_idx in self.default_params_values:
                    new_default_params_values[default_idx] = self.default_params_values[
                        default_idx
                    ]
        # Remove the value for the removed index if it was a default param
        if remove_index in self.default_params_values:
            del self.default_params_values[remove_index]
        self.default_params_values = new_default_params_values

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

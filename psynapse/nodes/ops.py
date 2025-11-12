from pathlib import Path
from typing import Any, Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QGraphicsProxyWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
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

        # Track default parameters and their values
        self.default_params = {}  # param_name -> default_value
        self.default_params_collapsed = True  # Initially collapsed

        # Convert schema params to input socket specifications
        inputs = []
        for idx, param in enumerate(schema.get("params", [])):
            param_name = param["name"].upper()  # e.g., "a" -> "A"
            param_type_str = param["type"]
            param_type = self._map_type(param_type_str)

            # Check if this parameter has a default value
            has_default = "default" in param
            if has_default:
                self.default_params[param_name] = param["default"]

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

        # Create collapsible control for default parameters
        if self.default_params:
            self._create_default_params_collapsible()

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

    def _create_default_params_collapsible(self):
        """Create collapsible control for default parameters."""
        # Create container widget
        container = QWidget()
        container.setFixedWidth(self.graphics.width - 20)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Create collapsible header
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)

        # Toggle button (arrow)
        self.collapse_button = QPushButton("▶")
        self.collapse_button.setFixedSize(20, 20)
        self.collapse_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #ffffff;
                font-size: 10px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
        """)
        self.collapse_button.clicked.connect(self._toggle_default_params)

        # Header label
        header_label = QLabel("Default Parameters")
        header_label.setStyleSheet(
            "color: #cccccc; font-size: 11px; font-weight: bold;"
        )

        header_layout.addWidget(self.collapse_button)
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        layout.addWidget(header_widget)

        # Add container to graphics
        proxy = QGraphicsProxyWidget(self.graphics)
        proxy.setWidget(container)
        proxy.setZValue(150)  # Above sockets but below buttons

        # Store references
        self.default_params_container = container
        self.default_params_proxy = proxy
        self.default_params_layout = layout

        # Initially hide the collapsible content and update socket visibility
        self._update_default_params_visibility()

        # Update node size and positions
        self._update_node_size()

    def _toggle_default_params(self):
        """Toggle the visibility of default parameter sockets."""
        self.default_params_collapsed = not self.default_params_collapsed
        self._update_default_params_visibility()
        self._update_node_size()

    def _update_default_params_visibility(self):
        """Update the visibility of default parameter sockets and UI elements."""
        # Update button text
        self.collapse_button.setText("▼" if not self.default_params_collapsed else "▶")

        # Show/hide default parameter sockets and their input widgets
        for socket in self.input_sockets:
            # Check if this socket corresponds to a default parameter
            socket_label = socket.label.upper()
            is_default_param = socket_label in self.default_params

            if is_default_param:
                # Always set the default value for default parameters
                default_value = self.default_params[socket_label]
                socket.value = default_value

                # Show/hide socket graphics and input widget based on collapsed state
                if socket.graphics:
                    socket.graphics.setVisible(not self.default_params_collapsed)
                if socket.label_item:
                    socket.label_item.setVisible(not self.default_params_collapsed)
                if socket.input_proxy:
                    socket.input_proxy.setVisible(not self.default_params_collapsed)
                    # Populate input widget with default value if it's visible
                    if not self.default_params_collapsed:
                        self._populate_input_widget_with_default(socket, default_value)

    def _populate_input_widget_with_default(self, socket, default_value):
        """Populate the input widget for a socket with its default value."""
        if not socket.input_widget:
            return

        # Populate based on socket data type
        if socket.data_type == SocketDataType.INT:
            # For int widgets, it might be a QSpinBox directly or wrapped in a container
            if hasattr(socket.input_widget, "setValue"):
                socket.input_widget.setValue(int(default_value))
            elif isinstance(socket.input_widget, QWidget):
                # Find QSpinBox in the container
                spinbox = socket.input_widget.findChild(QWidget)
                if spinbox and hasattr(spinbox, "setValue"):
                    spinbox.setValue(int(default_value))
        elif socket.data_type == SocketDataType.FLOAT:
            # For float widgets, it might be a QDoubleSpinBox directly or wrapped
            if hasattr(socket.input_widget, "setValue"):
                socket.input_widget.setValue(float(default_value))
            elif isinstance(socket.input_widget, QWidget):
                # Find QDoubleSpinBox in the container
                spinbox = socket.input_widget.findChild(QWidget)
                if spinbox and hasattr(spinbox, "setValue"):
                    spinbox.setValue(float(default_value))
        elif socket.data_type == SocketDataType.STRING:
            if hasattr(socket.input_widget, "setText"):
                socket.input_widget.setText(str(default_value))
        elif socket.data_type == SocketDataType.BOOL:
            # For bool widgets, it might be a container with QCheckBox
            if isinstance(socket.input_widget, QWidget):
                # Find QCheckBox in the container
                checkbox = socket.input_widget.findChild(QCheckBox)
                if checkbox and hasattr(checkbox, "setChecked"):
                    checkbox.setChecked(bool(default_value))
        # For dropdown (Literal types), the value is already set during socket creation

    def _update_node_size(self):
        """Update node size based on number of sockets."""
        socket_spacing = 30
        min_height = 100

        # Count visible sockets (exclude hidden default parameter sockets when collapsed)
        visible_sockets = 0
        for socket in self.input_sockets:
            socket_label = socket.label.upper()
            is_default_param = socket_label in self.default_params
            if not is_default_param or not self.default_params_collapsed:
                visible_sockets += 1

        # Add extra height for collapsible header if there are default params
        extra_height = 40 if self.default_params else 0  # Height for collapsible header

        calculated_height = 40 + visible_sockets * socket_spacing + extra_height + 60
        self.graphics.height = max(min_height, calculated_height)
        self.graphics.setRect(0, 0, self.graphics.width, self.graphics.height)
        self._position_sockets()
        if self.variadic_params:
            self._update_variadic_button_positions()
        if self.default_params:
            self._update_default_params_position()

    def _update_default_params_position(self):
        """Position the default parameters collapsible widget."""
        if not hasattr(self, "default_params_proxy"):
            return

        # Position the collapsible widget below the title
        y_position = 35  # Just below the title
        self.default_params_proxy.setPos(5, y_position)

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

    def _position_sockets(self):
        """Position sockets on the node, accounting for collapsed default parameters."""
        # Add sockets to graphics
        socket_spacing = 30
        current_y = 40

        # Add extra space for collapsible header if present
        if self.default_params:
            current_y += 40

        for i, socket in enumerate(self.input_sockets):
            # Check if this is a default parameter socket
            socket_label = socket.label.upper()
            is_default_param = socket_label in self.default_params

            # Position socket
            x = 0
            y = current_y + i * socket_spacing
            socket.graphics.setParentItem(self.graphics)
            socket.graphics.setPos(x, y)

            # Position label if it exists
            if socket.label_item:
                socket.label_item.setParentItem(self.graphics)
                # Position label to the right of the socket
                label_x = 15
                label_y = y - 8
                socket.label_item.setPos(label_x, label_y)

            # Position input widget if it exists
            if socket.input_widget:
                # Only create proxy widget if it doesn't exist
                if not hasattr(socket, "input_proxy") or socket.input_proxy is None:
                    socket.input_proxy = QGraphicsProxyWidget(self.graphics)
                    socket.input_proxy.setWidget(socket.input_widget)
                    # Set z-value to ensure input widgets appear above other elements
                    # Use higher z-value based on socket index to prevent overlap
                    socket.input_proxy.setZValue(100 + i)

                # Calculate available width for the widget
                # Start position: after socket and label
                widget_x = 15
                if socket.label_item:
                    widget_x = 15 + socket.label_item.boundingRect().width() + 5

                # End position: leave margin before right edge
                right_margin = 10
                available_width = self.graphics.width - widget_x - right_margin

                # Set minimum width to ensure widget is usable
                min_widget_width = 60
                widget_width = max(min_widget_width, available_width)

                # Resize the widget to fit available space
                socket.resize_input_widget(widget_width)

                # Position widget
                socket.input_proxy.setPos(widget_x, y - 10)

            # Hide/show socket elements based on default parameter state
            if is_default_param:
                visible = not self.default_params_collapsed
                if socket.graphics:
                    socket.graphics.setVisible(visible)
                if socket.label_item:
                    socket.label_item.setVisible(visible)
                if socket.input_proxy:
                    socket.input_proxy.setVisible(visible)

        # Position output sockets
        for i, socket in enumerate(self.output_sockets):
            x = self.graphics.width
            y = current_y + i * socket_spacing
            socket.graphics.setParentItem(self.graphics)
            socket.graphics.setPos(x, y)

            # Position label if it exists
            if socket.label_item:
                socket.label_item.setParentItem(self.graphics)
                # Position label to the left of the socket
                label_width = socket.label_item.boundingRect().width()
                label_x = x - label_width - 15
                label_y = y - 8
                socket.label_item.setPos(label_x, label_y)

    def execute(self) -> Any:
        """No-op execution - actual execution happens on the backend.

        The frontend nodes no longer need to execute operations since the backend's
        GraphExecutor handles all computation. This method exists only to satisfy
        the Node interface.
        """
        # Return None - actual execution is handled by the backend
        return None

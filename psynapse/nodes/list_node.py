from typing import Any

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


class ListNode(Node):
    """Node that collects multiple inputs into a list output."""

    def __init__(self):
        # Start with one input socket
        super().__init__(
            title="List",
            inputs=[("Item", SocketDataType.ANY)],
            outputs=[("List", SocketDataType.ANY)],
        )

        # Create container widget for buttons
        self.widget_container = QWidget()
        self.widget_layout = QHBoxLayout()
        self.widget_layout.setContentsMargins(0, 0, 0, 0)
        self.widget_layout.setSpacing(8)
        self.widget_layout.setAlignment(Qt.AlignCenter)
        self.widget_container.setLayout(self.widget_layout)

        # Create + button
        self.add_button = QPushButton("+")
        self.add_button.setFixedSize(30, 30)
        self.add_button.clicked.connect(self._add_socket)
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 18px;
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
        self.remove_button = QPushButton("−")
        self.remove_button.setFixedSize(30, 30)
        self.remove_button.clicked.connect(self._remove_socket)
        self.remove_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 18px;
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
        self.widget_layout.addWidget(self.add_button)
        self.widget_layout.addWidget(self.remove_button)

        # Add widget to graphics and center it
        self.widget_proxy = QGraphicsProxyWidget(self.graphics)
        self.widget_proxy.setWidget(self.widget_container)
        self.widget_proxy.setZValue(200)

        # Update node height to accommodate buttons
        self._update_node_size()

        # Position buttons in the middle of the node
        self._update_button_position()

    def _update_node_size(self):
        """Update node size based on number of sockets."""
        socket_spacing = 30
        min_height = 100
        calculated_height = 40 + len(self.input_sockets) * socket_spacing + 60
        self.graphics.height = max(min_height, calculated_height)
        self.graphics.setRect(0, 0, self.graphics.width, self.graphics.height)
        self._position_sockets()
        self._update_button_position()

    def _update_button_position(self):
        """Position buttons in the middle of the node."""
        # Center horizontally
        button_width = 68  # 30 + 8 spacing + 30
        button_x = (self.graphics.width - button_width) / 2

        # Position vertically in the middle of the node body (after title)
        # Find the middle point between first socket and last socket
        if len(self.input_sockets) > 0:
            first_socket_y = 40
            last_socket_y = 40 + (len(self.input_sockets) - 1) * 30
            middle_y = (first_socket_y + last_socket_y) / 2
        else:
            middle_y = 70

        # Center the button container vertically
        button_y = middle_y - 15  # Half of button height (30/2)
        self.widget_proxy.setPos(button_x, button_y)

    def _add_socket(self):
        """Add a new input socket."""
        # Create new socket with index matching its position in the list
        new_index = len(self.input_sockets)
        socket = Socket(
            self, new_index, SocketType.INPUT, "Item", SocketDataType.ANY, None, None
        )

        # Add to list
        self.input_sockets.append(socket)

        # Update inputs list for serialization
        self.inputs.append(("Item", SocketDataType.ANY))

        # Update node size and position sockets
        self._update_node_size()

        # Update all edges
        self.update_edges()

    def _remove_socket(self):
        """Remove the last input socket (if more than one exists)."""
        # Keep at least one socket
        if len(self.input_sockets) <= 1:
            return

        # Get the last socket
        last_socket = self.input_sockets[-1]

        # Remove all edges connected to this socket
        # Make a copy of the edges list since we'll be modifying it
        edges_to_remove = list(last_socket.edges)
        for edge in edges_to_remove:
            edge.remove()

        # Remove socket graphics from scene
        if last_socket.graphics.scene():
            last_socket.graphics.scene().removeItem(last_socket.graphics)

        # Remove label if it exists
        if last_socket.label_item and last_socket.label_item.scene():
            last_socket.label_item.scene().removeItem(last_socket.label_item)

        # Remove input widget if it exists
        if last_socket.input_proxy and last_socket.input_proxy.scene():
            last_socket.input_proxy.scene().removeItem(last_socket.input_proxy)

        # Remove from lists
        self.input_sockets.pop()
        self.inputs.pop()

        # Note: We don't need to update socket indices because:
        # 1. Serialization uses enumerate() which is based on list position
        # 2. Loading also uses enumerate() to map socket IDs
        # 3. The stored socket.index is only used for positioning, which uses enumerate()

        # Update node size and position sockets
        self._update_node_size()

        # Update all edges
        self.update_edges()

    def execute(self) -> Any:
        """Collect all input values into a list."""
        result = []
        for socket in self.input_sockets:
            value = socket.get_value()
            result.append(value)
        return result

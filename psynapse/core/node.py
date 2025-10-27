"""Base node class."""

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsProxyWidget,
    QGraphicsRectItem,
    QGraphicsTextItem,
)

from psynapse.core.socket import Socket, SocketType
from psynapse.core.socket_types import SocketDataType


class Node:
    """Base class for all nodes."""

    # Class-level error handler (set by editor)
    error_handler = None

    def __init__(
        self,
        title: str = "Node",
        inputs: list[tuple[str, SocketDataType]] = None,
        outputs: list[tuple[str, SocketDataType]] = None,
    ):
        self.title = title
        # Handle both old format (list of strings) and new format (list of tuples)
        self.inputs = inputs or []
        self.outputs = outputs or []
        self._last_error = None

        # Create graphics item
        self.graphics = NodeGraphics(self)

        # Create sockets
        self.input_sockets = []
        self.output_sockets = []

        for i, input_spec in enumerate(self.inputs):
            # Support both tuple (label, type) and string (label) formats
            if isinstance(input_spec, tuple):
                label, data_type = input_spec
            else:
                label = input_spec
                data_type = SocketDataType.ANY
            socket = Socket(self, i, SocketType.INPUT, label, data_type)
            self.input_sockets.append(socket)

        for i, output_spec in enumerate(self.outputs):
            if isinstance(output_spec, tuple):
                label, data_type = output_spec
            else:
                label = output_spec
                data_type = SocketDataType.ANY
            socket = Socket(self, i, SocketType.OUTPUT, label, data_type)
            self.output_sockets.append(socket)

        # Position sockets
        self._position_sockets()

    def _position_sockets(self):
        """Position sockets on the node."""
        # Add sockets to graphics
        socket_spacing = 30

        for i, socket in enumerate(self.input_sockets):
            x = 0
            y = 40 + i * socket_spacing
            socket.graphics.setParentItem(self.graphics)
            socket.graphics.setPos(x, y)

            # Position input widget if it exists
            if socket.input_widget:
                socket.input_proxy = QGraphicsProxyWidget(self.graphics)
                socket.input_proxy.setWidget(socket.input_widget)
                # Position widget to the right of the socket
                socket.input_proxy.setPos(20, y - 10)

        for i, socket in enumerate(self.output_sockets):
            x = self.graphics.width
            y = 40 + i * socket_spacing
            socket.graphics.setParentItem(self.graphics)
            socket.graphics.setPos(x, y)

    def set_position(self, x: float, y: float):
        """Set node position."""
        self.graphics.setPos(x, y)

    def get_socket_position(self, socket: Socket) -> tuple[float, float]:
        """Get socket position in scene coordinates."""
        return socket.get_position()

    def update_edges(self):
        """Update all connected edges."""
        for socket in self.input_sockets + self.output_sockets:
            for edge in socket.edges:
                edge.update_positions()

    def execute(self) -> Any:
        """Execute node - override in subclasses."""
        return None

    def execute_safe(self) -> Any:
        """Execute node with error handling."""
        try:
            self._last_error = None
            return self.execute()
        except Exception as e:
            self._last_error = e
            if Node.error_handler:
                Node.error_handler(self, e)
            # Return default value instead of propagating error
            if self.output_sockets:
                return self.output_sockets[0].value
            return None

    def get_input_value(self, index: int) -> Any:
        """Get value from input socket."""
        if index >= len(self.input_sockets):
            return None

        socket = self.input_sockets[index]
        return socket.get_value()


class NodeGraphics(QGraphicsRectItem):
    """Graphics representation of a node."""

    def __init__(self, node: Node):
        super().__init__()

        self.node = node

        # Dimensions
        self.width = 180
        self.height = 100 + max(len(node.inputs), len(node.outputs)) * 30
        self.edge_size = 10
        self.title_height = 30

        # Colors
        self._color_background = QColor("#212121")
        self._color_title = QColor("#2d2d2d")
        self._color_selected = QColor("#FFA637")

        # Pens and brushes
        self._pen_default = QPen(QColor("#000000"))
        self._pen_default.setWidth(2)
        self._pen_selected = QPen(self._color_selected)
        self._pen_selected.setWidth(3)

        self._brush_title = QBrush(self._color_title)
        self._brush_background = QBrush(self._color_background)

        # Set up
        self.setRect(0, 0, self.width, self.height)
        self.setPen(self._pen_default)
        self.setBrush(self._brush_background)

        # Make it movable and selectable
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)

        # Title text
        self.title_item = QGraphicsTextItem(self)
        self.title_item.setDefaultTextColor(Qt.white)
        self.title_item.setPlainText(node.title)
        self.title_item.setPos(self.edge_size, 0)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.title_item.setFont(font)

    def itemChange(self, change, value):
        """Handle item changes."""
        if change == QGraphicsItem.ItemPositionChange:
            # Update edges when node moves
            self.node.update_edges()
        return super().itemChange(change, value)

    def paint(self, painter: QPainter, option, widget=None):
        """Custom paint method."""
        # Draw title background
        painter.setBrush(self._brush_title)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(
            0, 0, self.width, self.title_height, self.edge_size, self.edge_size
        )
        painter.drawRect(
            0, self.title_height - self.edge_size, self.width, self.edge_size
        )

        # Draw main body
        painter.setBrush(self._brush_background)
        painter.drawRoundedRect(
            0,
            self.title_height,
            self.width,
            self.height - self.title_height,
            self.edge_size,
            self.edge_size,
        )
        painter.drawRect(0, self.title_height, self.width, self.edge_size)

        # Draw outline
        if self.isSelected():
            painter.setPen(self._pen_selected)
        else:
            painter.setPen(self._pen_default)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(
            0, 0, self.width, self.height, self.edge_size, self.edge_size
        )

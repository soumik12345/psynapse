from enum import Enum
from typing import TYPE_CHECKING

from PySide6.QtGui import QBrush, QColor, QPen
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QLineEdit,
)

from psynapse.core.socket_types import SocketDataType

if TYPE_CHECKING:
    from psynapse.core.node import Node


class SocketType(Enum):
    """Socket type enumeration."""

    INPUT = 1
    OUTPUT = 2


class Socket:
    """Logical socket data."""

    def __init__(
        self,
        node: "Node",
        index: int,
        socket_type: SocketType,
        label: str = "",
        data_type: SocketDataType = SocketDataType.ANY,
    ):
        self.node = node
        self.index = index
        self.socket_type = socket_type
        self.label = label
        self.data_type = data_type
        self.edges = []
        self.value = data_type.get_default_value()

        # Create graphics item
        self.graphics = SocketGraphics(self)

        # Create input widget for input sockets with editable types
        self.input_widget = None
        self.input_proxy = None
        if socket_type == SocketType.INPUT and data_type.needs_input_widget():
            self._create_input_widget()

    def get_position(self) -> tuple[float, float]:
        """Get socket position in scene coordinates."""
        return self.graphics.get_position()

    def add_edge(self, edge):
        """Add edge connected to this socket."""
        self.edges.append(edge)

    def remove_edge(self, edge):
        """Remove edge from this socket."""
        if edge in self.edges:
            self.edges.remove(edge)

    def has_edge(self) -> bool:
        """Check if socket has any edges."""
        return len(self.edges) > 0

    def _create_input_widget(self):
        """Create input widget for editable socket types."""
        self.input_widget = QLineEdit()
        self.input_widget.setMaximumWidth(80)
        self.input_widget.setMaximumHeight(20)

        # Set placeholder based on type
        if self.data_type == SocketDataType.INT:
            self.input_widget.setPlaceholderText("0")
        elif self.data_type == SocketDataType.FLOAT:
            self.input_widget.setPlaceholderText("0.0")
        elif self.data_type == SocketDataType.STRING:
            self.input_widget.setPlaceholderText('""')

        # Set initial value
        self.input_widget.setText(str(self.value))

        # Connect value change
        self.input_widget.textChanged.connect(self._on_input_changed)

        # Style the widget
        self.input_widget.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 3px;
                padding: 2px 4px;
                font-size: 10px;
            }
            QLineEdit:focus {
                border: 1px solid #FF7700;
            }
        """)

    def _on_input_changed(self, text: str):
        """Handle input widget text change."""
        if text:
            self.value = self.data_type.validate(text)
        else:
            self.value = self.data_type.get_default_value()

    def get_value(self):
        """Get the current value from input or connected edge."""
        # If connected, get value from edge
        if self.has_edge():
            edge = self.edges[0]
            if edge.start_socket and edge.start_socket.node:
                return edge.start_socket.node.execute_safe()

        # Otherwise return local value
        return self.value

    def set_input_widget_visible(self, visible: bool):
        """Set visibility of input widget based on connection state."""
        if self.input_proxy:
            self.input_proxy.setVisible(visible)


class SocketGraphics(QGraphicsEllipseItem):
    """Graphics representation of a socket."""

    def __init__(self, socket: Socket):
        super().__init__()

        self.socket = socket
        self.radius = 8

        # Set up appearance
        self._color_background = QColor("#FF7700")
        self._color_outline = QColor("#000000")

        self.setBrush(QBrush(self._color_background))
        self.setPen(QPen(self._color_outline, 2))

        # Set size
        self.setRect(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)

        # Make it selectable and hoverable
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
        self.setAcceptHoverEvents(True)

    def get_position(self) -> tuple[float, float]:
        """Get position in scene coordinates."""
        pos = self.scenePos()
        return (pos.x(), pos.y())

    def hoverEnterEvent(self, event):
        """Change appearance on hover."""
        self._color_background = QColor("#FFAA00")
        self.setBrush(QBrush(self._color_background))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Restore appearance after hover."""
        self._color_background = QColor("#FF7700")
        self.setBrush(QBrush(self._color_background))
        super().hoverLeaveEvent(event)

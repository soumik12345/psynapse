"""Connection edge between sockets."""

from typing import Optional

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem

from psynapse.core.socket import Socket


class Edge:
    """Logical edge connecting two sockets."""

    def __init__(
        self, start_socket: Optional[Socket] = None, end_socket: Optional[Socket] = None
    ):
        self.start_socket = start_socket
        self.end_socket = end_socket

        # Create graphics item
        self.graphics = EdgeGraphics(self)

        # Register with sockets
        if self.start_socket:
            self.start_socket.add_edge(self)
        if self.end_socket:
            self.end_socket.add_edge(self)

    def update_positions(self):
        """Update edge path based on socket positions."""
        if self.start_socket and self.end_socket:
            start_pos = self.start_socket.get_position()
            end_pos = self.end_socket.get_position()
            self.graphics.set_source(start_pos[0], start_pos[1])
            self.graphics.set_destination(end_pos[0], end_pos[1])

    def remove(self):
        """Remove edge from sockets and scene."""
        if self.start_socket:
            self.start_socket.remove_edge(self)
        if self.end_socket:
            self.end_socket.remove_edge(self)
            # Show input widget when disconnected
            from psynapse.socket import SocketType

            if self.end_socket.socket_type == SocketType.INPUT:
                self.end_socket.set_input_widget_visible(True)
        if self.graphics.scene():
            self.graphics.scene().removeItem(self.graphics)


class EdgeGraphics(QGraphicsPathItem):
    """Graphics representation of an edge."""

    def __init__(self, edge: Edge):
        super().__init__()

        self.edge = edge

        self.pos_source = QPointF(0, 0)
        self.pos_destination = QPointF(200, 100)

        # Appearance
        self._color = QColor("#00FF00")
        self._pen = QPen(self._color)
        self._pen.setWidth(3)

        self.setPen(self._pen)
        self.setZValue(-1)  # Draw behind nodes

        # Make selectable
        self.setFlag(QGraphicsItem.ItemIsSelectable)

        self.update_path()

    def set_source(self, x: float, y: float):
        """Set source position."""
        self.pos_source = QPointF(x, y)
        self.update_path()

    def set_destination(self, x: float, y: float):
        """Set destination position."""
        self.pos_destination = QPointF(x, y)
        self.update_path()

    def update_path(self):
        """Update the bezier curve path."""
        path = QPainterPath()
        path.moveTo(self.pos_source)

        # Calculate control points for bezier curve
        dx = self.pos_destination.x() - self.pos_source.x()
        dy = self.pos_destination.y() - self.pos_source.y()

        # Horizontal bezier
        ctrl_offset = abs(dx) * 0.5
        ctrl1 = QPointF(self.pos_source.x() + ctrl_offset, self.pos_source.y())
        ctrl2 = QPointF(
            self.pos_destination.x() - ctrl_offset, self.pos_destination.y()
        )

        path.cubicTo(ctrl1, ctrl2, self.pos_destination)

        self.setPath(path)

    def paint(self, painter: QPainter, option, widget=None):
        """Custom paint to handle selection."""
        if self.isSelected():
            self._pen.setColor(QColor("#FFFFFF"))
        else:
            self._pen.setColor(self._color)
        self.setPen(self._pen)
        super().paint(painter, option, widget)

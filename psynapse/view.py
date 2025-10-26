"""View for the node editor."""

from typing import Optional

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsView

from psynapse.edge import Edge
from psynapse.scene import NodeScene
from psynapse.socket import Socket, SocketGraphics, SocketType


class NodeView(QGraphicsView):
    """View for displaying and interacting with the node editor."""

    def __init__(self, scene: NodeScene, parent=None):
        super().__init__(scene, parent)

        self.node_scene = scene

        # View settings
        self.setRenderHints(
            QPainter.Antialiasing
            | QPainter.TextAntialiasing
            | QPainter.SmoothPixmapTransform
        )
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.RubberBandDrag)

        # Connection state
        self.temp_edge: Optional[Edge] = None
        self.dragging_edge = False
        self.drag_start_socket: Optional[Socket] = None

        # Zoom settings
        self.zoom_factor = 1.0
        self.zoom_step = 1.2
        self.zoom_range = [0.3, 3.0]

    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())

            # Check if clicking on a socket
            if isinstance(item, SocketGraphics):
                self.drag_start_socket = item.socket
                self.dragging_edge = True

                # Create temporary edge
                pos = item.socket.get_position()
                self.temp_edge = Edge()
                self.temp_edge.graphics.set_source(pos[0], pos[1])
                self.temp_edge.graphics.set_destination(pos[0], pos[1])
                self.scene().addItem(self.temp_edge.graphics)
                return

        elif event.button() == Qt.RightButton:
            # Enable panning with right mouse button
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            # Fake left button press to start dragging
            fake_event = QEvent(QEvent.MouseButtonPress)
            super().mousePressEvent(event)
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move."""
        if self.dragging_edge and self.temp_edge:
            # Update temporary edge endpoint
            scene_pos = self.mapToScene(event.pos())
            pos = self.drag_start_socket.get_position()
            self.temp_edge.graphics.set_source(pos[0], pos[1])
            self.temp_edge.graphics.set_destination(scene_pos.x(), scene_pos.y())

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if event.button() == Qt.LeftButton:
            if self.dragging_edge:
                item = self.itemAt(event.pos())

                # Check if released on a socket
                if isinstance(item, SocketGraphics):
                    end_socket = item.socket

                    # Validate connection
                    if self._can_connect(self.drag_start_socket, end_socket):
                        # Remove any existing connections to input socket
                        if end_socket.socket_type == SocketType.INPUT:
                            for edge in end_socket.edges[:]:
                                edge.remove()

                        # Create real edge
                        if self.drag_start_socket.socket_type == SocketType.OUTPUT:
                            edge = Edge(self.drag_start_socket, end_socket)
                            # Hide input widget when connected
                            end_socket.set_input_widget_visible(False)
                        else:
                            edge = Edge(end_socket, self.drag_start_socket)
                            # Hide input widget when connected
                            self.drag_start_socket.set_input_widget_visible(False)

                        self.scene().addItem(edge.graphics)
                        edge.update_positions()

                # Clean up temporary edge
                if self.temp_edge:
                    self.temp_edge.remove()
                    self.temp_edge = None

                self.dragging_edge = False
                self.drag_start_socket = None
                return

        elif event.button() == Qt.RightButton:
            # Restore drag mode after panning
            self.setDragMode(QGraphicsView.RubberBandDrag)

        super().mouseReleaseEvent(event)

    def _can_connect(self, socket1: Socket, socket2: Socket) -> bool:
        """Check if two sockets can be connected."""
        if socket1 == socket2:
            return False
        if socket1.node == socket2.node:
            return False
        if socket1.socket_type == socket2.socket_type:
            return False
        return True

    def wheelEvent(self, event):
        """Handle mouse wheel for zooming."""
        # Calculate zoom factor
        if event.angleDelta().y() > 0:
            zoom_factor = self.zoom_step
        else:
            zoom_factor = 1 / self.zoom_step

        # Apply zoom limits
        self.zoom_factor *= zoom_factor
        if self.zoom_factor < self.zoom_range[0]:
            self.zoom_factor = self.zoom_range[0]
            zoom_factor = self.zoom_range[0] / (self.zoom_factor / zoom_factor)
        elif self.zoom_factor > self.zoom_range[1]:
            self.zoom_factor = self.zoom_range[1]
            zoom_factor = self.zoom_range[1] / (self.zoom_factor / zoom_factor)

        # Apply zoom
        self.scale(zoom_factor, zoom_factor)

    def keyPressEvent(self, event):
        """Handle key press."""
        # Check for Ctrl+D (Cmd+D on Mac)
        if event.key() == Qt.Key_D and event.modifiers() & Qt.ControlModifier:
            # Delete selected items
            for item in self.scene().selectedItems():
                # Handle edge deletion
                if hasattr(item, "edge"):
                    item.edge.remove()
                # Handle node deletion
                elif hasattr(item, "node"):
                    node = item.node
                    # Remove all connected edges
                    for socket in node.input_sockets + node.output_sockets:
                        for edge in socket.edges[:]:
                            edge.remove()
                    # Remove node
                    self.scene().removeItem(item)

        super().keyPressEvent(event)

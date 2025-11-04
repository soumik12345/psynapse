from typing import Any, Dict

from PySide6.QtCore import QMimeData, QPoint, Qt
from PySide6.QtGui import QDrag, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from psynapse.nodes.object_node import ObjectNode
from psynapse.nodes.ops import OpNode
from psynapse.nodes.view_node import ViewNode


def create_op_node_factory(schema: Dict[str, Any]):
    """Create a factory function that creates an OpNode from a schema.

    Args:
        schema: Node schema from the backend

    Returns:
        Factory function that creates an OpNode instance
    """

    def factory():
        return OpNode(schema)

    return factory


# Default node types that don't come from schemas (client-side only)
DEFAULT_NODE_TYPES = [
    (ObjectNode, "Object"),
    (ViewNode, "View"),
]


class NodeLibraryItem(QLabel):
    """A single node item in the library that can be dragged."""

    def __init__(self, node_class, node_name, parent=None):
        super().__init__(parent)
        self.node_class = node_class
        self.node_name = node_name

        # Set up the label
        self.setText(node_name)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setMinimumHeight(40)
        self.setMaximumHeight(40)
        self.setCursor(Qt.PointingHandCursor)

        # Style
        self.setStyleSheet(
            """
            NodeLibraryItem {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 2px solid #5a5a5a;
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: bold;
            }
            NodeLibraryItem:hover {
                background-color: #5a5a5a;
                border: 2px solid #6a6a6a;
            }
        """
        )

    def mousePressEvent(self, event):
        """Start drag operation when mouse is pressed."""
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()

            # Store node class name in mime data
            mime_data.setText(self.node_class.__name__)
            drag.setMimeData(mime_data)

            # Create drag pixmap
            pixmap = QPixmap(self.size())
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setOpacity(0.7)
            self.render(painter, QPoint(0, 0))
            painter.end()

            drag.setPixmap(pixmap)
            drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))

            # Execute drag
            drag.exec(Qt.CopyAction)


class CollapsibleSection(QWidget):
    """A collapsible section with a header and content area."""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.is_expanded = True

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with toggle button
        self.header = QWidget()
        self.header.setCursor(Qt.PointingHandCursor)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(4, 4, 4, 4)
        header_layout.setSpacing(8)

        # Arrow indicator
        self.arrow = QLabel("▼")
        self.arrow.setFixedWidth(12)
        self.arrow.setStyleSheet(
            """
            QLabel {
                color: #aaaaaa;
                font-size: 10px;
            }
        """
        )
        header_layout.addWidget(self.arrow)

        # Title label
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            """
            QLabel {
                color: #aaaaaa;
                font-size: 11px;
                font-weight: bold;
            }
        """
        )
        header_layout.addWidget(self.title_label, 1)

        # Style the header
        self.header.setStyleSheet(
            """
            QWidget {
                background-color: transparent;
            }
            QWidget:hover {
                background-color: #454545;
            }
        """
        )

        layout.addWidget(self.header)

        # Content container
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)

        layout.addWidget(self.content)

        # Connect header click to toggle
        self.header.mousePressEvent = self._toggle

    def _toggle(self, event):
        """Toggle the expanded/collapsed state."""
        self.is_expanded = not self.is_expanded

        if self.is_expanded:
            self.arrow.setText("▼")
            self.content.show()
        else:
            self.arrow.setText("▶")
            self.content.hide()

    def add_item(self, widget):
        """Add a widget to the content area."""
        self.content_layout.addWidget(widget)


class NodeLibraryPanel(QWidget):
    """Panel displaying available nodes that can be added to the editor."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.node_types = []
        self.container_layout = None  # Store reference to update later
        self.setup_ui()

    def add_schema_nodes(self, schemas: list[Dict[str, Any]]):
        """Add nodes from backend schemas to the container layout.

        Args:
            schemas: List of node schemas from the backend
        """
        if not schemas or not self.container_layout:
            return

        # Create operations section
        ops_section = CollapsibleSection("Operations")
        for schema in schemas:
            node_name = schema["name"]
            node_factory = create_op_node_factory(schema)
            # Store with a unique class name based on the schema
            node_factory.__name__ = f"OpNode_{schema['name']}"
            self.node_types.append((node_factory, node_name))
            node_item = NodeLibraryItem(node_factory, node_name)
            ops_section.add_item(node_item)

        # Insert at the beginning (before default nodes)
        self.container_layout.insertWidget(0, ops_section)
        self.container_layout.insertSpacing(1, 8)

    def add_default_nodes(self, container_layout):
        """Add the default nodes to the container layout."""
        self.node_types.extend(DEFAULT_NODE_TYPES)
        default_section = CollapsibleSection("Default Nodes")
        for node_class, node_name in DEFAULT_NODE_TYPES:
            node_item = NodeLibraryItem(node_class, node_name)
            default_section.add_item(node_item)
        container_layout.addWidget(default_section)
        container_layout.addSpacing(8)

    def load_schemas(self, schemas: list[Dict[str, Any]]):
        """Load and display nodes from backend schemas.

        Args:
            schemas: List of node schemas from the backend
        """
        self.add_schema_nodes(schemas)

    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Title
        title = QLabel("Node Library")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            """
            QLabel {
                background-color: #2d2d2d;
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                padding: 12px;
                border-bottom: 2px solid #1a1a1a;
            }
        """
        )
        main_layout.addWidget(title)

        # Scroll area for nodes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.NoFrame)

        # Container for node items
        container = QWidget()
        self.container_layout = QVBoxLayout(container)
        self.container_layout.setContentsMargins(8, 8, 8, 8)
        self.container_layout.setSpacing(8)

        # Default nodes are added at the end (after schema nodes will be added)
        # Note: Schema nodes will be added via load_schemas() call from editor

        self.add_default_nodes(self.container_layout)

        # Add stretch to push everything to the top
        self.container_layout.addStretch()

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

        # Style the panel
        self.setStyleSheet(
            """
            NodeLibraryPanel {
                background-color: #3a3a3a;
            }
            QScrollArea {
                background-color: #3a3a3a;
                border: none;
            }
        """
        )

    def get_node_class_map(self):
        """Return a mapping of node class names to node classes."""
        return {node_class.__name__: node_class for node_class, _ in self.node_types}

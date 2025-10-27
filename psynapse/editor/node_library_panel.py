"""Node library panel for browsing and adding nodes."""

from PySide6.QtCore import QMimeData, QPoint, Qt
from PySide6.QtGui import QDrag, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from psynapse.core.nodes import AddNode, MultiplyNode, SubtractNode, ViewNode


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


class NodeLibraryPanel(QWidget):
    """Panel displaying available nodes that can be added to the editor."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Available node types
        self.node_types = [
            (AddNode, "Add"),
            (SubtractNode, "Subtract"),
            (MultiplyNode, "Multiply"),
            (ViewNode, "View"),
        ]

        self._setup_ui()

    def _setup_ui(self):
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
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(8, 8, 8, 8)
        container_layout.setSpacing(8)

        # Add section labels and nodes
        self._add_section(
            container_layout,
            "Math Operations",
            [
                (AddNode, "Add"),
                (SubtractNode, "Subtract"),
                (MultiplyNode, "Multiply"),
            ],
        )

        container_layout.addSpacing(8)

        self._add_section(
            container_layout,
            "Display",
            [
                (ViewNode, "View"),
            ],
        )

        # Add stretch to push everything to the top
        container_layout.addStretch()

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

    def _add_section(self, layout, section_name, nodes):
        """Add a section with nodes to the layout."""
        # Section label
        section_label = QLabel(section_name)
        section_label.setStyleSheet(
            """
            QLabel {
                color: #aaaaaa;
                font-size: 11px;
                font-weight: bold;
                padding: 4px 4px;
            }
        """
        )
        layout.addWidget(section_label)

        # Add node items
        for node_class, node_name in nodes:
            node_item = NodeLibraryItem(node_class, node_name)
            layout.addWidget(node_item)

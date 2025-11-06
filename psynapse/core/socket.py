from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsTextItem,
    QHBoxLayout,
    QLineEdit,
    QSpinBox,
    QWidget,
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
        options: Optional[List[str]] = None,
    ):
        self.node = node
        self.index = index
        self.socket_type = socket_type
        self.label = label
        self.data_type = data_type
        self.options = options  # For Literal types with specific allowed values
        self.edges = []
        self.value = data_type.get_default_value()

        # Create graphics item
        self.graphics = SocketGraphics(self)

        # Create label text item
        self.label_item = None
        self._create_label()

        # Create input widget for input sockets with editable types
        self.input_widget = None
        self.input_proxy = None
        if socket_type == SocketType.INPUT:
            # Create dropdown for options (Literal types)
            if options:
                self._create_input_widget()
            # Create standard widgets for editable types
            elif data_type.needs_input_widget():
                self._create_input_widget()

    def get_position(self) -> tuple[float, float]:
        """Get socket position in scene coordinates."""
        return self.graphics.get_position()

    def _create_label(self):
        """Create label text item for the socket."""
        if not self.label:
            return

        self.label_item = QGraphicsTextItem()
        self.label_item.setDefaultTextColor(Qt.white)
        self.label_item.setPlainText(self.label)

        # Set font
        font = QFont()
        font.setPointSize(9)
        self.label_item.setFont(font)

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
        # If options are provided (Literal types), create dropdown
        if self.options:
            self.input_widget = self._create_dropdown_widget()
        elif self.data_type == SocketDataType.INT:
            self.input_widget = self._create_int_widget()
        elif self.data_type == SocketDataType.FLOAT:
            self.input_widget = self._create_float_widget()
        elif self.data_type == SocketDataType.STRING:
            self.input_widget = self._create_string_widget()
        elif self.data_type == SocketDataType.BOOL:
            self.input_widget = self._create_bool_widget()
        else:
            # Fallback for other types
            self.input_widget = self._create_string_widget()

    def _create_int_widget(self):
        """Create integer spinbox widget."""
        widget = QSpinBox()
        widget.setMinimum(-999999)
        widget.setMaximum(999999)
        widget.setValue(int(self.value) if self.value else 0)
        widget.setFixedWidth(80)
        widget.setFixedHeight(26)
        widget.setAlignment(Qt.AlignCenter)
        widget.valueChanged.connect(self._on_int_changed)

        widget.setStyleSheet("""
            QSpinBox {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 3px;
                padding: 2px 4px;
                font-size: 10px;
            }
            QSpinBox:focus {
                border: 1px solid #FF7700;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #2d2d2d;
                border: 1px solid #444444;
                width: 16px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #FF7700;
            }
        """)

        return widget

    def _create_float_widget(self):
        """Create float spinbox widget."""
        widget = QDoubleSpinBox()
        widget.setMinimum(-999999.0)
        widget.setMaximum(999999.0)
        widget.setDecimals(4)
        widget.setSingleStep(0.1)
        widget.setValue(float(self.value) if self.value else 0.0)
        widget.setFixedWidth(80)
        widget.setFixedHeight(26)
        widget.setAlignment(Qt.AlignCenter)
        widget.valueChanged.connect(self._on_float_changed)

        widget.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 3px;
                padding: 2px 4px;
                font-size: 10px;
            }
            QDoubleSpinBox:focus {
                border: 1px solid #FF7700;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                background-color: #2d2d2d;
                border: 1px solid #444444;
                width: 16px;
            }
            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
                background-color: #FF7700;
            }
        """)

        return widget

    def _create_string_widget(self):
        """Create string input widget."""
        widget = QLineEdit()
        widget.setPlaceholderText("Enter text...")
        widget.setText(str(self.value) if self.value else "")
        widget.setFixedWidth(80)
        widget.setFixedHeight(26)
        widget.setAlignment(Qt.AlignCenter)
        widget.textChanged.connect(self._on_string_changed)

        widget.setStyleSheet("""
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

        return widget

    def _create_bool_widget(self):
        """Create boolean checkbox widget."""
        # Create a container to center the checkbox
        container = QWidget()
        container.setFixedWidth(80)
        container.setFixedHeight(26)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        widget = QCheckBox()
        widget.setChecked(bool(self.value) if self.value else False)
        widget.stateChanged.connect(self._on_bool_changed)

        widget.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                font-size: 10px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                background-color: #1a1a1a;
                border: 1px solid #444444;
                border-radius: 3px;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #FF7700;
            }
            QCheckBox::indicator:checked {
                background-color: #FF7700;
                border: 1px solid #FF7700;
            }
        """)

        layout.addWidget(widget)
        return container

    def _create_dropdown_widget(self):
        """Create dropdown widget for Literal types with options."""
        widget = QComboBox()
        widget.setFixedWidth(100)
        widget.setFixedHeight(26)

        # Add options to the dropdown
        for option in self.options:
            widget.addItem(str(option))

        # Set default value to first option
        if self.options:
            self.value = str(self.options[0])

        widget.currentTextChanged.connect(self._on_dropdown_changed)

        widget.setStyleSheet("""
            QComboBox {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 10px;
            }
            QComboBox:focus {
                border: 1px solid #FF7700;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #ffffff;
                selection-background-color: #FF7700;
                border: 1px solid #444444;
            }
        """)

        return widget

    def _on_int_changed(self, value: int):
        """Handle integer spinbox value change."""
        self.value = value

    def _on_float_changed(self, value: float):
        """Handle float spinbox value change."""
        self.value = value

    def _on_string_changed(self, text: str):
        """Handle string input text change."""
        self.value = text if text else ""

    def _on_bool_changed(self, state: int):
        """Handle checkbox state change."""
        self.value = bool(state)

    def _on_dropdown_changed(self, text: str):
        """Handle dropdown selection change."""
        self.value = text

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

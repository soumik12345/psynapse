from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGraphicsProxyWidget,
    QGraphicsTextItem,
    QHBoxLayout,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from psynapse.core.node import Node
from psynapse.core.socket_types import SocketDataType


class AddNode(Node):
    """Node that adds two numbers."""

    def __init__(self):
        super().__init__(
            title="Add",
            inputs=[("A", SocketDataType.FLOAT), ("B", SocketDataType.FLOAT)],
            outputs=[("Result", SocketDataType.FLOAT)],
        )

    def execute(self) -> Any:
        """Add two input values."""
        a = self.get_input_value(0)
        b = self.get_input_value(1)

        if a is None:
            a = 0.0
        if b is None:
            b = 0.0

        try:
            result = float(a) + float(b)
            self.output_sockets[0].value = result
            return result
        except (TypeError, ValueError):
            return 0.0


class SubtractNode(Node):
    """Node that subtracts two numbers."""

    def __init__(self):
        super().__init__(
            title="Subtract",
            inputs=[("A", SocketDataType.FLOAT), ("B", SocketDataType.FLOAT)],
            outputs=[("Result", SocketDataType.FLOAT)],
        )

    def execute(self) -> Any:
        """Subtract B from A."""
        a = self.get_input_value(0)
        b = self.get_input_value(1)

        if a is None:
            a = 0.0
        if b is None:
            b = 0.0

        try:
            result = float(a) - float(b)
            self.output_sockets[0].value = result
            return result
        except (TypeError, ValueError):
            return 0.0


class MultiplyNode(Node):
    """Node that multiplies two numbers."""

    def __init__(self):
        super().__init__(
            title="Multiply",
            inputs=[("A", SocketDataType.FLOAT), ("B", SocketDataType.FLOAT)],
            outputs=[("Result", SocketDataType.FLOAT)],
        )

    def execute(self) -> Any:
        """Multiply two input values."""
        a = self.get_input_value(0)
        b = self.get_input_value(1)

        if a is None:
            a = 1.0
        if b is None:
            b = 1.0

        try:
            result = float(a) * float(b)
            self.output_sockets[0].value = result
            return result
        except (TypeError, ValueError):
            return 0.0


class ViewNode(Node):
    """Node that displays a value."""

    def __init__(self):
        super().__init__(
            title="View", inputs=[("Value", SocketDataType.ANY)], outputs=[]
        )

        # Create text display
        self.display_text = QGraphicsTextItem(self.graphics)
        self.display_text.setDefaultTextColor(Qt.white)
        self.display_text.setPos(10, 50)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.display_text.setFont(font)
        self.display_text.setPlainText("None")

        self.cached_value = None

    def execute(self) -> Any:
        """Display input value."""
        value = self.get_input_value(0)

        # Update display
        if value != self.cached_value:
            self.cached_value = value
            if value is None:
                display_str = "None"
            elif isinstance(value, float):
                # Format floats nicely
                display_str = f"{value:.4g}"
            else:
                display_str = str(value)
            self.display_text.setPlainText(display_str)

        return value


class ObjectNode(Node):
    """Node that creates and outputs a typed value."""

    def __init__(self):
        super().__init__(
            title="Object",
            inputs=[],
            outputs=[("Value", SocketDataType.ANY)],
        )

        self.current_value = None
        self.current_type = SocketDataType.INT

        # Create container widget
        self.widget_container = QWidget()
        self.widget_layout = QVBoxLayout()
        self.widget_layout.setContentsMargins(0, 0, 0, 0)
        self.widget_layout.setSpacing(8)
        self.widget_layout.setAlignment(Qt.AlignCenter)
        self.widget_container.setLayout(self.widget_layout)

        # Create type selector
        self.type_selector = QComboBox()
        self.type_selector.addItem("int", SocketDataType.INT)
        self.type_selector.addItem("float", SocketDataType.FLOAT)
        self.type_selector.addItem("str", SocketDataType.STRING)
        self.type_selector.addItem("bool", SocketDataType.BOOL)
        self.type_selector.setFixedWidth(160)
        self.type_selector.currentIndexChanged.connect(self._on_type_changed)

        # Style the type selector
        self.type_selector.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 3px;
                padding: 5px 8px;
                padding-right: 25px;
                font-size: 11px;
            }
            QComboBox:hover {
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

        self.widget_layout.addWidget(self.type_selector)

        # Placeholder for input widget
        self.input_widget = None
        self._create_input_widget()

        # Add widget to graphics and center it
        self.widget_proxy = QGraphicsProxyWidget(self.graphics)
        self.widget_proxy.setWidget(self.widget_container)

        # Center the widget container horizontally in the node
        widget_x = (self.graphics.width - 160) / 2
        self.widget_proxy.setPos(widget_x, 40)

        # Update node height to accommodate widgets
        self.graphics.height = 160
        self.graphics.setRect(0, 0, self.graphics.width, self.graphics.height)

    def _on_type_changed(self, index: int):
        """Handle type selector change."""
        self.current_type = self.type_selector.itemData(index)
        self._create_input_widget()

    def _create_input_widget(self):
        """Create appropriate input widget based on selected type."""
        # Remove old input widget if exists
        if self.input_widget:
            self.widget_layout.removeWidget(self.input_widget)
            self.input_widget.deleteLater()
            self.input_widget = None

        # Create new input widget based on type
        if self.current_type == SocketDataType.INT:
            self.input_widget = self._create_int_widget()
        elif self.current_type == SocketDataType.FLOAT:
            self.input_widget = self._create_float_widget()
        elif self.current_type == SocketDataType.STRING:
            self.input_widget = self._create_string_widget()
        elif self.current_type == SocketDataType.BOOL:
            self.input_widget = self._create_bool_widget()

        if self.input_widget:
            self.widget_layout.addWidget(self.input_widget)

        # Update the value
        self._update_value()

    def _create_int_widget(self):
        """Create integer spinbox widget."""
        widget = QSpinBox()
        widget.setMinimum(-999999)
        widget.setMaximum(999999)
        widget.setValue(0)
        widget.setFixedWidth(160)
        widget.setAlignment(Qt.AlignCenter)
        widget.valueChanged.connect(self._update_value)

        widget.setStyleSheet("""
            QSpinBox {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 3px;
                padding: 5px 8px;
                font-size: 11px;
            }
            QSpinBox:focus {
                border: 1px solid #FF7700;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #2d2d2d;
                border: 1px solid #444444;
                width: 20px;
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
        widget.setValue(0.0)
        widget.setFixedWidth(160)
        widget.setAlignment(Qt.AlignCenter)
        widget.valueChanged.connect(self._update_value)

        widget.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 3px;
                padding: 5px 8px;
                font-size: 11px;
            }
            QDoubleSpinBox:focus {
                border: 1px solid #FF7700;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                background-color: #2d2d2d;
                border: 1px solid #444444;
                width: 20px;
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
        widget.setFixedWidth(160)
        widget.setAlignment(Qt.AlignCenter)
        widget.textChanged.connect(self._update_value)

        widget.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 3px;
                padding: 5px 8px;
                font-size: 11px;
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
        container.setFixedWidth(160)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        widget = QCheckBox("Value")
        widget.setChecked(False)
        widget.stateChanged.connect(self._update_value)

        widget.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
                font-size: 11px;
                padding: 2px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
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

    def _update_value(self):
        """Update the current value from the input widget."""
        if self.input_widget is None:
            self.current_value = None
            return

        if self.current_type == SocketDataType.INT:
            self.current_value = self.input_widget.value()
        elif self.current_type == SocketDataType.FLOAT:
            self.current_value = self.input_widget.value()
        elif self.current_type == SocketDataType.STRING:
            self.current_value = self.input_widget.text()
        elif self.current_type == SocketDataType.BOOL:
            # For bool, input_widget is a container, find the checkbox
            checkbox = self.input_widget.findChild(QCheckBox)
            if checkbox:
                self.current_value = checkbox.isChecked()

        # Update output socket value
        if self.output_sockets:
            self.output_sockets[0].value = self.current_value

    def execute(self) -> Any:
        """Return the current value."""
        return self.current_value

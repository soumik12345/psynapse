from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QGraphicsTextItem

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

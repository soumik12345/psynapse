from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QGraphicsTextItem,
)

from psynapse.core.node import Node
from psynapse.core.socket_types import SocketDataType


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

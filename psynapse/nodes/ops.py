from typing import Any, Dict

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QGraphicsTextItem,
)

from psynapse.core.node import Node
from psynapse.core.socket_types import SocketDataType


class OpNode(Node):
    """Generalized operation node that can be created from a node schema.

    This node is dynamically configured based on the schema received from the backend.
    The actual execution logic is handled by the backend's GraphExecutor, so this node
    only serves as a visual representation in the frontend.
    """

    def __init__(self, schema: Dict[str, Any]):
        """Initialize an OpNode from a schema.

        Args:
            schema: Node schema dictionary containing:
                - name: Node type name (e.g., "add", "subtract")
                - params: List of input parameter definitions
                - returns: List of output definitions
        """
        self.node_type = schema["name"]

        # Convert schema params to input socket specifications
        inputs = []
        for param in schema.get("params", []):
            param_name = param["name"].upper()  # e.g., "a" -> "A"
            param_type = self._map_type(param["type"])
            inputs.append((param_name, param_type))

        # Convert schema returns to output socket specifications
        outputs = []
        for return_spec in schema.get("returns", []):
            return_name = return_spec["name"].capitalize()  # e.g., "result" -> "Result"
            return_type = self._map_type(return_spec["type"])
            outputs.append((return_name, return_type))

        # Initialize with proper title (capitalize the node type name)
        title = schema["name"].capitalize()
        super().__init__(title=title, inputs=inputs, outputs=outputs)

    def _map_type(self, type_str: str) -> SocketDataType:
        """Map schema type string to SocketDataType.

        Args:
            type_str: Type string from schema (e.g., "float", "any")

        Returns:
            Corresponding SocketDataType
        """
        type_mapping = {
            "float": SocketDataType.FLOAT,
            "int": SocketDataType.INT,
            "string": SocketDataType.STRING,
            "bool": SocketDataType.BOOL,
            "any": SocketDataType.ANY,
        }
        return type_mapping.get(type_str.lower(), SocketDataType.ANY)

    def execute(self) -> Any:
        """No-op execution - actual execution happens on the backend.

        The frontend nodes no longer need to execute operations since the backend's
        GraphExecutor handles all computation. This method exists only to satisfy
        the Node interface.
        """
        # Return None - actual execution is handled by the backend
        return None


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

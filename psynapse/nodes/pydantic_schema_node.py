import json
import typing
from typing import Any

import pydantic
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGraphicsProxyWidget,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from psynapse.core.node import Node
from psynapse.core.socket_types import SocketDataType


class PydanticSchemaNode(Node):
    """Node that creates and outputs a Pydantic model type from field definitions."""

    def __init__(self):
        super().__init__(
            title="PydanticSchema",
            inputs=[],
            outputs=[("Schema", SocketDataType.ANY)],
        )

        # Store schema entries as list of dicts: [{"field": str, "type": str, "default_value": Any}, ...]
        self.entries = [{"field": "", "type": "str", "default_value": None}]

        # Store schema name (default to "DynamicSchema")
        self.schema_name = "DynamicSchema"

        # Create container widget
        self.widget_container = QWidget()
        self.widget_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.widget_layout = QVBoxLayout()
        self.widget_layout.setContentsMargins(4, 4, 4, 4)
        self.widget_layout.setSpacing(8)
        self.widget_layout.setAlignment(Qt.AlignCenter)
        self.widget_container.setLayout(self.widget_layout)

        # Create schema name input row
        schema_name_row = QWidget()
        schema_name_layout = QHBoxLayout()
        schema_name_layout.setContentsMargins(0, 0, 0, 0)
        schema_name_layout.setSpacing(8)
        schema_name_row.setLayout(schema_name_layout)

        # Schema name label
        schema_name_label = QLabel("Schema name:")
        schema_name_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        schema_name_layout.addWidget(schema_name_label)

        # Schema name input
        self.schema_name_input = QLineEdit()
        self.schema_name_input.setText(self.schema_name)
        self.schema_name_input.setPlaceholderText("e.g. UserSchema, ProductModel")
        self.schema_name_input.textChanged.connect(self._on_schema_name_changed)
        self.schema_name_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 3px;
                padding: 3px 5px;
                font-size: 10px;
            }
            QLineEdit:hover {
                border: 1px solid #FF7700;
            }
            QLineEdit:focus {
                border: 1px solid #FF7700;
                background-color: #333333;
            }
        """)
        schema_name_layout.addWidget(self.schema_name_input)

        # Add schema name row to main layout
        self.widget_layout.addWidget(schema_name_row)

        # Create table widget
        self.table = QTableWidget()
        self.table.setColumnCount(4)  # Delete button, Field, Type, Default Value
        self.table.setHorizontalHeaderLabels(["", "Field", "Type", "Default Value"])
        # Set size policy to prevent expansion beyond container
        self.table.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # Use minimum sizes instead of fixed sizes to allow dynamic resizing
        self.table.setMinimumWidth(200)
        self.table.setMinimumHeight(80)
        # Set column resize modes
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Fixed
        )  # Delete button column
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )  # Field column
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Stretch
        )  # Type column - stretchable for compound types
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.Stretch
        )  # Default Value column
        # Set delete button column width (smaller than row height)
        self.table.setColumnWidth(0, 22)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        self.table.setAlternatingRowColors(True)
        self.table.cellChanged.connect(self._on_cell_changed)

        # Style the table
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 3px;
                gridline-color: #444444;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 4px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #FF7700;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #444444;
                font-weight: bold;
            }
        """)

        self.widget_layout.addWidget(self.table)

        # Populate table with initial entry
        self._populate_table()

        # Add widget to graphics and center it
        self.widget_proxy = QGraphicsProxyWidget(self.graphics)
        self.widget_proxy.setWidget(self.widget_container)
        self.widget_proxy.setZValue(200)

        # Set initial node width to accommodate table
        if self.graphics.width < 320:
            self.graphics.width = 320
            self.graphics.setRect(0, 0, self.graphics.width, self.graphics.height)

        # Update node height to accommodate widgets (will be recalculated)
        self._update_node_size()

        # Update widget sizes and positions
        self._update_widget_sizes()

        # Override the graphics mouseMoveEvent to handle widget resizing
        self._original_mouse_move = self.graphics.mouseMoveEvent
        self.graphics.mouseMoveEvent = self._on_graphics_mouse_move

    def _parse_type_string(self, type_str: str) -> type:
        """Parse a type string into a Python type.

        Supports simple types (str, int, bool, etc.) and compound types from typing
        (List[str], Dict[str, Any], Optional[int], etc.)
        """
        if not type_str or not type_str.strip():
            return str

        type_str = type_str.strip()

        # Create a safe namespace with typing module contents and builtins
        safe_globals = {
            "Any": Any,
            "List": typing.List,
            "Dict": typing.Dict,
            "Optional": typing.Optional,
            "Union": typing.Union,
            "Tuple": typing.Tuple,
            "Set": typing.Set,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
        }

        try:
            # Try to evaluate the type string
            parsed_type = eval(type_str, safe_globals, {})
            return parsed_type
        except Exception:
            # If parsing fails, default to str
            return str

    def _populate_table(self):
        """Populate the table with current entries."""
        # Disconnect cellChanged signal temporarily to avoid recursive updates
        self.table.cellChanged.disconnect(self._on_cell_changed)

        # Clear all existing widgets before repopulating
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                widget = self.table.cellWidget(row, col)
                if widget:
                    self.table.removeCellWidget(row, col)
                    widget.deleteLater()

        # Set row count: entries + 1 for the add button row
        self.table.setRowCount(len(self.entries) + 1)

        # Set row height for all rows
        row_height = 25
        button_size = 16  # Smaller button size for better containment
        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, row_height)

        for row, entry in enumerate(self.entries):
            # Delete button column (column 0)
            remove_button = QPushButton("−")
            remove_button.setFixedSize(button_size, button_size)
            remove_button.clicked.connect(
                lambda checked=False, r=row: self._remove_row(r)
            )
            remove_button.setStyleSheet("""
                QPushButton {
                    background-color: #3a3a3a;
                    color: #ffffff;
                    border: 1px solid #555555;
                    border-radius: 3px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #4a4a4a;
                    border: 1px solid #666666;
                }
                QPushButton:pressed {
                    background-color: #2a2a2a;
                }
            """)
            self.table.setCellWidget(row, 0, remove_button)

            # Field column (column 1)
            field_item = QTableWidgetItem(entry["field"])
            self.table.setItem(row, 1, field_item)

            # Type column (column 2) - use QLineEdit for text input
            type_input = QLineEdit()
            type_input.setText(entry["type"])
            type_input.setPlaceholderText("e.g. str, List[int], Dict[str, Any]")

            # Use a closure to capture the row value correctly
            def make_type_changed_handler(r):
                return lambda: self._on_type_text_changed(r)

            type_input.textChanged.connect(make_type_changed_handler(row))
            type_input.setStyleSheet("""
                QLineEdit {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #444444;
                    border-radius: 3px;
                    padding: 3px 5px;
                    font-size: 10px;
                }
                QLineEdit:hover {
                    border: 1px solid #FF7700;
                }
                QLineEdit:focus {
                    border: 1px solid #FF7700;
                    background-color: #333333;
                }
            """)
            self.table.setCellWidget(row, 2, type_input)

            # Default Value column (column 3)
            default_value_str = self._value_to_string(
                entry["default_value"], entry["type"]
            )
            default_value_item = QTableWidgetItem(default_value_str)
            self.table.setItem(row, 3, default_value_item)

        # Add "+" button row at the bottom
        add_row_index = len(self.entries)
        add_button = QPushButton("+")
        add_button.setFixedSize(button_size, button_size)
        add_button.clicked.connect(self._add_row)
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border: 1px solid #666666;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
        """)
        self.table.setCellWidget(add_row_index, 0, add_button)

        # Make the add button row cells non-editable (except the button)
        for col in range(1, 4):
            empty_item = QTableWidgetItem("")
            empty_item.setFlags(empty_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(add_row_index, col, empty_item)

        # Reconnect cellChanged signal
        self.table.cellChanged.connect(self._on_cell_changed)

    def _value_to_string(self, value: Any, type_str: str) -> str:
        """Convert a value to string representation for display."""
        if value is None:
            return ""

        # Determine if it's a bool type
        if type_str.strip().lower() in ["bool", "boolean"]:
            return "True" if value else "False"

        # Determine if it's a list/List type
        if type_str.strip().lower().startswith("list"):
            if isinstance(value, list):
                return json.dumps(value)
            return json.dumps([])

        # Determine if it's a dict/Dict type
        if type_str.strip().lower().startswith("dict"):
            if isinstance(value, dict):
                return json.dumps(value)
            return json.dumps({})

        return str(value)

    def _string_to_value(self, value_str: str, type_str: str) -> Any:
        """Convert a string to the appropriate type."""
        if not value_str.strip():
            return None  # Empty default value means optional field

        try:
            type_lower = type_str.strip().lower()

            # For list/List types, try JSON parsing
            if type_lower.startswith("list"):
                if value_str.strip():
                    try:
                        parsed = json.loads(value_str)
                        if isinstance(parsed, list):
                            return parsed
                    except json.JSONDecodeError:
                        pass
                return []

            # For dict/Dict types, try JSON parsing
            elif type_lower.startswith("dict"):
                if value_str.strip():
                    try:
                        parsed = json.loads(value_str)
                        if isinstance(parsed, dict):
                            return parsed
                    except json.JSONDecodeError:
                        pass
                return {}

            # For bool type
            elif type_lower in ["bool", "boolean"]:
                return value_str.strip().lower() in ["true", "1", "yes"]

            # For int type
            elif type_lower == "int":
                return int(value_str)

            # For float type
            elif type_lower == "float":
                return float(value_str)

            # For str type or anything else
            else:
                return value_str
        except Exception:
            return None

    def _on_cell_changed(self, row: int, column: int):
        """Handle cell value changes."""
        # Ignore changes to the add button row
        if row >= len(self.entries):
            return

        if column == 1:  # Field column
            field_item = self.table.item(row, 1)
            if field_item:
                self.entries[row]["field"] = field_item.text()
        elif column == 3:  # Default Value column
            default_value_item = self.table.item(row, 3)
            if default_value_item:
                type_input = self.table.cellWidget(row, 2)
                if type_input:
                    type_str = type_input.text()
                    value_str = default_value_item.text()
                    self.entries[row]["default_value"] = self._string_to_value(
                        value_str, type_str
                    )

        self._update_output()

    def _on_type_text_changed(self, row: int):
        """Handle type text changes."""
        # Ignore changes if row is out of bounds
        if row >= len(self.entries):
            return

        type_input = self.table.cellWidget(row, 2)
        if type_input:
            new_type_str = type_input.text()
            self.entries[row]["type"] = new_type_str

            # Convert default value to new type
            default_value_item = self.table.item(row, 3)
            if default_value_item:
                value_str = default_value_item.text()
                self.entries[row]["default_value"] = self._string_to_value(
                    value_str, new_type_str
                )
                # Update display
                new_value_str = self._value_to_string(
                    self.entries[row]["default_value"], new_type_str
                )
                # Temporarily block signals to avoid recursion
                self.table.blockSignals(True)
                default_value_item.setText(new_value_str)
                self.table.blockSignals(False)

        self._update_output()

    def _on_schema_name_changed(self, text: str):
        """Handle schema name changes."""
        self.schema_name = text.strip() if text.strip() else "DynamicSchema"
        self._update_output()

    def _add_row(self):
        """Add a new row to the table."""
        self.entries.append({"field": "", "type": "str", "default_value": None})
        self._populate_table()
        self._update_node_size()
        self._update_widget_sizes()
        self._update_output()

    def _remove_row(self, row: int):
        """Remove a specific row from the table."""
        if len(self.entries) > 1 and 0 <= row < len(self.entries):
            self.entries.pop(row)
            self._populate_table()
            self._update_node_size()
            self._update_widget_sizes()
            self._update_output()

    def _update_output(self):
        """Update the output Pydantic model type."""
        # Don't store the type object in the socket value (it's not JSON serializable)
        # The type will be created on-the-fly in execute() method
        # For backend execution, entries are serialized in params
        if self.output_sockets:
            # Set a marker value to indicate this node has a value (but don't store the type)
            self.output_sockets[0].value = None

    def execute(self) -> Any:
        """Return the current Pydantic model type."""
        try:
            schema_dict = {}
            for entry in self.entries:
                field_name = entry["field"].strip()
                if field_name:  # Only add non-empty fields
                    python_type = self._parse_type_string(entry["type"])
                    default_value = entry["default_value"]

                    # Format: { field_name: type } or { field_name: (type, default_value) }
                    if default_value is not None:
                        schema_dict[field_name] = (python_type, default_value)
                    else:
                        schema_dict[field_name] = python_type

            # Create Pydantic model with the custom schema name
            schema_name = self.schema_name if self.schema_name else "DynamicSchema"
            if schema_dict:
                model_type = pydantic.create_model(schema_name, **schema_dict)
            else:
                # Empty schema - create a model with no fields
                model_type = pydantic.create_model(schema_name)

            return model_type
        except Exception as e:
            return None

    def _on_graphics_mouse_move(self, event):
        """Handle mouse move on graphics item, updating widget sizes when resizing."""
        # Call original mouseMoveEvent
        self._original_mouse_move(event)

        # If we're resizing, update widget sizes
        if self.graphics.is_resizing:
            self._update_widget_sizes()

    def _update_node_size(self):
        """Update node size based on number of entries and content."""
        # Calculate minimum required height:
        # - Title bar: ~30px
        # - Top margin: ~10px
        # - Layout top margin: ~4px
        # - Schema name input row: ~30px
        # - Layout spacing: ~8px
        # - Table header: ~30px
        # - Table rows: ~25px per row (entries + 1 for add button row)
        # - Layout bottom margin: ~4px
        # - Bottom margin: ~10px
        # - Output socket space: ~10px
        min_row_height = 25
        num_rows = max(1, len(self.entries) + 1)  # +1 for add button row
        table_content_height = 30 + (num_rows * min_row_height)  # header + rows
        schema_name_row_height = 30 + 8  # schema name input + spacing

        min_height = (
            30 + 10 + 4 + schema_name_row_height + table_content_height + 4 + 10 + 10
        )
        min_height = max(
            210, min_height
        )  # Ensure minimum node height (increased for schema name input)

        # Update node height if needed
        if self.graphics.height < min_height:
            self.graphics.height = min_height
            self.graphics.setRect(0, 0, self.graphics.width, self.graphics.height)
            self._position_sockets()

    def _update_widget_sizes(self):
        """Update the sizes of widgets to fit the current node size."""
        # Calculate available width (leave margins on both sides)
        # Account for layout margins (4px on each side) and node margins
        layout_margins = 8  # 4px on each side from layout
        node_margins = 8  # Additional margin from node edges
        total_horizontal_margin = layout_margins + node_margins

        # Ensure we don't exceed node width
        max_available_width = self.graphics.width - total_horizontal_margin
        available_width = max(200, max_available_width)

        # Calculate available height for table:
        # - Title bar: ~30px
        # - Top margin: ~8px
        # - Layout top margin: ~4px
        # - Schema name input row: ~30px
        # - Layout spacing: ~8px
        # - Layout bottom margin: ~4px
        # - Bottom margin: ~8px
        # - Output socket space: ~10px
        schema_name_row_height = 30 + 8  # schema name input + spacing
        header_and_margins = 30 + 8 + 4 + schema_name_row_height + 4 + 8 + 10
        max_available_height = self.graphics.height - header_and_margins
        available_height = max(60, max_available_height)

        # Ensure container doesn't exceed node boundaries
        container_width = min(
            available_width, self.graphics.width - total_horizontal_margin
        )
        # Container height = table height
        container_height = min(
            available_height,
            self.graphics.height - 30 - 10,  # node height - title - bottom margin
        )

        # Update container size - set fixed size to prevent expansion
        self.widget_container.setFixedSize(container_width, container_height)
        self.widget_container.setMaximumSize(container_width, container_height)

        # Update table size - ensure it fits within container
        # Account for layout margins (4px top/bottom)
        table_width = container_width - 8  # Account for layout margins
        table_height = available_height
        self.table.setFixedSize(table_width, table_height)
        self.table.setMaximumSize(table_width, table_height)

        # Update delete button column width to accommodate button with padding
        button_size = 16
        self.table.setColumnWidth(0, 22)  # Slightly wider than button for padding

        # Center the widget container horizontally in the node
        widget_x = max(0, (self.graphics.width - container_width) / 2)
        widget_y = 50  # Start below output socket to give it space on the left
        self.widget_proxy.setPos(widget_x, widget_y)

        # Force update to ensure sizes are applied
        self.widget_container.updateGeometry()
        self.table.updateGeometry()

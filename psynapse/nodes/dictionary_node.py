import json
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGraphicsProxyWidget,
    QHeaderView,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from psynapse.core.node import Node
from psynapse.core.socket_types import SocketDataType


class DictionaryNode(Node):
    """Node that creates and outputs a dictionary from key-value pairs."""

    def __init__(self):
        super().__init__(
            title="Dictionary",
            inputs=[],
            outputs=[("Dictionary", SocketDataType.ANY)],
        )

        # Store dictionary entries as list of dicts: [{"key": str, "type": SocketDataType, "value": Any}, ...]
        self.entries = [{"key": "", "type": SocketDataType.STRING, "value": ""}]

        # Create container widget
        self.widget_container = QWidget()
        self.widget_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.widget_layout = QVBoxLayout()
        self.widget_layout.setContentsMargins(4, 4, 4, 4)
        self.widget_layout.setSpacing(8)
        self.widget_layout.setAlignment(Qt.AlignCenter)
        self.widget_container.setLayout(self.widget_layout)

        # Create table widget
        self.table = QTableWidget()
        self.table.setColumnCount(4)  # Delete button, Key, Type, Value
        self.table.setHorizontalHeaderLabels(["", "Key", "Type", "Value"])
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
        )  # Key column
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Fixed
        )  # Type column - fixed width for dropdown
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.Stretch
        )  # Value column
        # Set delete button column width (smaller than row height)
        self.table.setColumnWidth(0, 22)
        # Set Type column width to accommodate dropdown properly
        self.table.setColumnWidth(2, 90)
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

            # Key column (column 1)
            key_item = QTableWidgetItem(entry["key"])
            self.table.setItem(row, 1, key_item)

            # Type column (column 2) - use QComboBox
            type_combo = QComboBox()
            type_combo.addItem("str", SocketDataType.STRING)
            type_combo.addItem("int", SocketDataType.INT)
            type_combo.addItem("float", SocketDataType.FLOAT)
            type_combo.addItem("bool", SocketDataType.BOOL)
            type_combo.addItem("list", SocketDataType.LIST)
            type_combo.addItem("dict", SocketDataType.DICT)
            # Find the index matching the entry's type
            current_index = 0
            for i in range(type_combo.count()):
                if type_combo.itemData(i) == entry["type"]:
                    current_index = i
                    break
            type_combo.setCurrentIndex(current_index)

            # Use a closure to capture the row value correctly
            def make_type_changed_handler(r):
                return lambda index: self._on_type_changed(r, index)

            type_combo.currentIndexChanged.connect(make_type_changed_handler(row))
            type_combo.setStyleSheet("""
                QComboBox {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #444444;
                    border-radius: 3px;
                    padding: 3px 5px;
                    padding-right: 20px;
                    font-size: 10px;
                    min-width: 50px;
                }
                QComboBox:hover {
                    border: 1px solid #FF7700;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
                QComboBox::down-arrow {
                    width: 10px;
                    height: 10px;
                }
                QComboBox QAbstractItemView {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    selection-background-color: #FF7700;
                    selection-color: #ffffff;
                    border: 1px solid #444444;
                    padding: 2px;
                    min-width: 60px;
                }
                QComboBox QAbstractItemView::item {
                    padding: 4px 8px;
                    min-height: 20px;
                }
                QComboBox QAbstractItemView::item:hover {
                    background-color: #3a3a3a;
                }
            """)
            # Set minimum width to ensure dropdown items display fully
            type_combo.setMinimumWidth(60)
            self.table.setCellWidget(row, 2, type_combo)

            # Value column (column 3)
            value_str = self._value_to_string(entry["value"], entry["type"])
            value_item = QTableWidgetItem(value_str)
            self.table.setItem(row, 3, value_item)

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

    def _value_to_string(self, value: Any, data_type: SocketDataType) -> str:
        """Convert a value to string representation for display."""
        if value is None:
            return ""
        if data_type == SocketDataType.BOOL:
            return "True" if value else "False"
        if data_type == SocketDataType.LIST:
            if isinstance(value, list):
                return json.dumps(value)
            return json.dumps([])
        if data_type == SocketDataType.DICT:
            if isinstance(value, dict):
                return json.dumps(value)
            return json.dumps({})
        return str(value)

    def _string_to_value(self, value_str: str, data_type: SocketDataType) -> Any:
        """Convert a string to the appropriate type."""
        if not value_str.strip():
            return data_type.get_default_value()

        try:
            # For list and dict, try JSON parsing first
            if data_type == SocketDataType.LIST:
                if value_str.strip():
                    try:
                        parsed = json.loads(value_str)
                        if isinstance(parsed, list):
                            return parsed
                    except json.JSONDecodeError:
                        pass
                return data_type.get_default_value()
            elif data_type == SocketDataType.DICT:
                if value_str.strip():
                    try:
                        parsed = json.loads(value_str)
                        if isinstance(parsed, dict):
                            return parsed
                    except json.JSONDecodeError:
                        pass
                return data_type.get_default_value()
            else:
                return data_type.validate(value_str)
        except Exception:
            return data_type.get_default_value()

    def _on_cell_changed(self, row: int, column: int):
        """Handle cell value changes."""
        # Ignore changes to the add button row
        if row >= len(self.entries):
            return

        if column == 1:  # Key column
            key_item = self.table.item(row, 1)
            if key_item:
                self.entries[row]["key"] = key_item.text()
        elif column == 3:  # Value column
            value_item = self.table.item(row, 3)
            if value_item:
                type_combo = self.table.cellWidget(row, 2)
                if type_combo:
                    data_type = type_combo.itemData(type_combo.currentIndex())
                    value_str = value_item.text()
                    self.entries[row]["value"] = self._string_to_value(
                        value_str, data_type
                    )

        self._update_output()

    def _on_type_changed(self, row: int, index: int):
        """Handle type selection changes."""
        # Ignore changes if row is out of bounds
        if row >= len(self.entries):
            return

        type_combo = self.table.cellWidget(row, 2)
        if type_combo:
            new_type = type_combo.itemData(index)
            old_type = self.entries[row]["type"]
            self.entries[row]["type"] = new_type

            # Convert value to new type
            value_item = self.table.item(row, 3)
            if value_item:
                value_str = value_item.text()
                self.entries[row]["value"] = self._string_to_value(value_str, new_type)
                # Update display
                new_value_str = self._value_to_string(
                    self.entries[row]["value"], new_type
                )
                value_item.setText(new_value_str)

        self._update_output()

    def _add_row(self):
        """Add a new row to the table."""
        self.entries.append({"key": "", "type": SocketDataType.STRING, "value": ""})
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
        """Update the output dictionary."""
        result_dict = {}
        for entry in self.entries:
            key = entry["key"].strip()
            if key:  # Only add non-empty keys
                result_dict[key] = entry["value"]

        # Update output socket value
        if self.output_sockets:
            self.output_sockets[0].value = result_dict

    def execute(self) -> Any:
        """Return the current dictionary."""
        result_dict = {}
        for entry in self.entries:
            key = entry["key"].strip()
            if key:  # Only add non-empty keys
                result_dict[key] = entry["value"]
        return result_dict

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
        # - Table header: ~30px
        # - Table rows: ~25px per row (entries + 1 for add button row)
        # - Layout bottom margin: ~4px
        # - Bottom margin: ~10px
        # - Output socket space: ~10px
        min_row_height = 25
        num_rows = max(1, len(self.entries) + 1)  # +1 for add button row
        table_content_height = 30 + (num_rows * min_row_height)  # header + rows

        min_height = 30 + 10 + 4 + table_content_height + 4 + 10 + 10
        min_height = max(
            180, min_height
        )  # Ensure minimum node height (increased for better containment)

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
        # - Layout bottom margin: ~4px
        # - Bottom margin: ~8px
        # - Output socket space: ~10px
        header_and_margins = 30 + 8 + 4 + 4 + 8 + 10
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
        # Ensure Type column maintains proper width for dropdown
        self.table.setColumnWidth(2, 90)

        # Center the widget container horizontally in the node
        widget_x = max(0, (self.graphics.width - container_width) / 2)
        widget_y = 50  # Start below output socket to give it space on the left
        self.widget_proxy.setPos(widget_x, widget_y)

        # Force update to ensure sizes are applied
        self.widget_container.updateGeometry()
        self.table.updateGeometry()

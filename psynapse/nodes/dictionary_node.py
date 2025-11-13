from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGraphicsProxyWidget,
    QHBoxLayout,
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
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Key", "Type", "Value"])
        # Set size policy to prevent expansion beyond container
        self.table.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # Use minimum sizes instead of fixed sizes to allow dynamic resizing
        self.table.setMinimumWidth(200)
        self.table.setMinimumHeight(80)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
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

        # Create button container
        self.button_container = QWidget()
        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(8)
        self.button_layout.setAlignment(Qt.AlignCenter)
        self.button_container.setLayout(self.button_layout)

        # Create + button
        self.add_button = QPushButton("+")
        self.add_button.setFixedSize(30, 30)
        self.add_button.clicked.connect(self._add_row)
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)

        # Create - button
        self.remove_button = QPushButton("−")
        self.remove_button.setFixedSize(30, 30)
        self.remove_button.clicked.connect(self._remove_row)
        self.remove_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c62828;
            }
        """)

        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.remove_button)
        self.widget_layout.addWidget(self.button_container)

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

        self.table.setRowCount(len(self.entries))
        for row, entry in enumerate(self.entries):
            # Key column
            key_item = QTableWidgetItem(entry["key"])
            self.table.setItem(row, 0, key_item)

            # Type column - use QComboBox
            type_combo = QComboBox()
            type_combo.addItem("str", SocketDataType.STRING)
            type_combo.addItem("int", SocketDataType.INT)
            type_combo.addItem("float", SocketDataType.FLOAT)
            type_combo.addItem("bool", SocketDataType.BOOL)
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
                    font-size: 10px;
                }
                QComboBox:hover {
                    border: 1px solid #FF7700;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 15px;
                }
                QComboBox QAbstractItemView {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    selection-background-color: #FF7700;
                    border: 1px solid #444444;
                }
            """)
            self.table.setCellWidget(row, 1, type_combo)

            # Value column
            value_str = self._value_to_string(entry["value"], entry["type"])
            value_item = QTableWidgetItem(value_str)
            self.table.setItem(row, 2, value_item)

        # Reconnect cellChanged signal
        self.table.cellChanged.connect(self._on_cell_changed)

    def _value_to_string(self, value: Any, data_type: SocketDataType) -> str:
        """Convert a value to string representation for display."""
        if value is None:
            return ""
        if data_type == SocketDataType.BOOL:
            return "True" if value else "False"
        return str(value)

    def _string_to_value(self, value_str: str, data_type: SocketDataType) -> Any:
        """Convert a string to the appropriate type."""
        if not value_str.strip():
            return data_type.get_default_value()

        try:
            return data_type.validate(value_str)
        except Exception:
            return data_type.get_default_value()

    def _on_cell_changed(self, row: int, column: int):
        """Handle cell value changes."""
        if column == 0:  # Key column
            key_item = self.table.item(row, 0)
            if key_item:
                self.entries[row]["key"] = key_item.text()
        elif column == 2:  # Value column
            value_item = self.table.item(row, 2)
            if value_item:
                type_combo = self.table.cellWidget(row, 1)
                if type_combo:
                    data_type = type_combo.itemData(type_combo.currentIndex())
                    value_str = value_item.text()
                    self.entries[row]["value"] = self._string_to_value(
                        value_str, data_type
                    )

        self._update_output()

    def _on_type_changed(self, row: int, index: int):
        """Handle type selection changes."""
        type_combo = self.table.cellWidget(row, 1)
        if type_combo:
            new_type = type_combo.itemData(index)
            old_type = self.entries[row]["type"]
            self.entries[row]["type"] = new_type

            # Convert value to new type
            value_item = self.table.item(row, 2)
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

    def _remove_row(self):
        """Remove the last row from the table."""
        if len(self.entries) > 1:
            self.entries.pop()
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
        # - Table rows: ~25px per row (minimum 1 row)
        # - Layout spacing: ~8px (between table and buttons)
        # - Button container: ~38px (30px button + 8px spacing)
        # - Layout bottom margin: ~4px
        # - Bottom margin: ~10px
        # - Output socket space: ~10px
        min_row_height = 25
        num_rows = max(1, len(self.entries))
        table_content_height = 30 + (num_rows * min_row_height)  # header + rows

        min_height = 30 + 10 + 4 + table_content_height + 8 + 38 + 4 + 10 + 10
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
        # - Button container: ~38px (30px button + 8px spacing)
        # - Layout bottom margin: ~4px
        # - Bottom margin: ~8px
        # - Output socket space: ~10px
        header_and_margins = 30 + 8 + 4 + 38 + 4 + 8 + 10
        max_available_height = self.graphics.height - header_and_margins
        available_height = max(60, max_available_height)

        # Ensure container doesn't exceed node boundaries
        container_width = min(
            available_width, self.graphics.width - total_horizontal_margin
        )
        # Container height = table height + button container + layout spacing
        container_height = min(
            available_height + 38 + 8,  # table + buttons + spacing
            self.graphics.height - 30 - 10,  # node height - title - bottom margin
        )

        # Update container size - set fixed size to prevent expansion
        self.widget_container.setFixedSize(container_width, container_height)
        self.widget_container.setMaximumSize(container_width, container_height)

        # Update table size - ensure it fits within container
        # Account for layout margins (4px top/bottom) and spacing (8px to buttons)
        table_width = container_width - 8  # Account for layout margins
        table_height = available_height
        self.table.setFixedSize(table_width, table_height)
        self.table.setMaximumSize(table_width, table_height)

        # Center the widget container horizontally in the node
        widget_x = max(0, (self.graphics.width - container_width) / 2)
        widget_y = 30  # Start right below title bar
        self.widget_proxy.setPos(widget_x, widget_y)

        # Force update to ensure sizes are applied
        self.widget_container.updateGeometry()
        self.table.updateGeometry()

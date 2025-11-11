from io import BytesIO
from typing import Any

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QGraphicsProxyWidget,
    QGraphicsTextItem,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from psynapse.core.node import Node
from psynapse.core.socket_types import SocketDataType


class ViewNode(Node):
    """Node that displays a value."""

    def __init__(self):
        super().__init__(
            title="View", inputs=[("Value", SocketDataType.ANY)], outputs=[]
        )

        # Increase node width for better tree display
        self.graphics.width = 250
        self.graphics.setRect(0, 0, self.graphics.width, self.graphics.height)
        # Reposition sockets after width change
        self._position_sockets()

        # Create text display for simple values
        self.display_text = QGraphicsTextItem(self.graphics)
        self.display_text.setDefaultTextColor(Qt.white)
        self.display_text.setPos(10, 50)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.display_text.setFont(font)
        self.display_text.setPlainText("None")
        self.display_text.setVisible(True)

        # Create tree widget for dictionaries (initially hidden)
        self.tree_widget = None
        self.tree_proxy = None

        # Create image label for displaying images (initially hidden)
        self.image_label = None
        self.image_proxy = None

        self.cached_value = None
        self.is_showing_tree = False
        self.is_showing_image = False

        # Override the graphics mouseMoveEvent to handle content resizing
        self._original_mouse_move = self.graphics.mouseMoveEvent
        self.graphics.mouseMoveEvent = self._on_graphics_mouse_move

    def _on_graphics_mouse_move(self, event):
        """Handle mouse move on graphics item, updating content sizes when resizing."""
        # Call original mouseMoveEvent
        self._original_mouse_move(event)

        # If we're resizing, update content sizes
        if self.graphics.is_resizing:
            self._update_content_sizes()

    def _update_content_sizes(self):
        """Update the sizes of text and tree widgets to fit the current node size."""
        # Update text display width
        if self.display_text:
            # Set text width to allow wrapping within node bounds
            text_width = max(50, self.graphics.width - 20)
            self.display_text.setTextWidth(text_width)

        # Update tree widget sizes
        if self.tree_widget and self.tree_proxy:
            # Calculate available space (accounting for margins, title bar, etc.)
            available_width = max(100, self.graphics.width - 30)
            available_height = max(80, self.graphics.height - 70)

            # Update tree widget size constraints for both width AND height
            self.tree_widget.setMinimumWidth(available_width)
            self.tree_widget.setMaximumWidth(available_width)
            self.tree_widget.setMinimumHeight(available_height)
            self.tree_widget.setMaximumHeight(available_height)

            # Update container widget size for both width AND height
            if self.tree_proxy.widget():
                container = self.tree_proxy.widget()
                container.setFixedWidth(available_width + 10)
                container.setFixedHeight(available_height + 10)

        # Update image label sizes
        if self.image_label and self.image_proxy:
            # Calculate available space
            available_width = max(100, self.graphics.width - 30)
            available_height = max(80, self.graphics.height - 70)

            # Update image label size
            self.image_label.setMinimumWidth(available_width)
            self.image_label.setMaximumWidth(available_width)
            self.image_label.setMinimumHeight(available_height)
            self.image_label.setMaximumHeight(available_height)

            # Update container widget size
            if self.image_proxy.widget():
                container = self.image_proxy.widget()
                container.setFixedWidth(available_width + 10)
                container.setFixedHeight(available_height + 10)

            # Re-scale the image to fit new size
            if hasattr(self, "_current_pixmap") and self._current_pixmap:
                scaled_pixmap = self._current_pixmap.scaled(
                    available_width,
                    available_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.image_label.setPixmap(scaled_pixmap)

    def _create_tree_widget(self):
        """Create the tree widget for displaying dictionaries."""
        if self.tree_widget is not None:
            return

        # Create a container widget
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border: 1px solid #555;
                border-radius: 4px;
            }
            QTreeWidget {
                background-color: #2b2b2b;
                color: white;
                border: none;
                font-size: 11px;
            }
            QTreeWidget::item {
                padding: 2px;
            }
            QTreeWidget::item:hover {
                background-color: #3a3a3a;
            }
            QTreeWidget::item:selected {
                background-color: #4a4a4a;
            }
            QTreeWidget::branch:closed:has-children {
                image: none;
            }
            QTreeWidget::branch:open:has-children {
                image: none;
            }
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        # Initial sizes - will be updated dynamically on resize
        initial_width = max(100, self.graphics.width - 30)
        initial_height = max(80, self.graphics.height - 70)
        self.tree_widget.setMinimumWidth(initial_width)
        self.tree_widget.setMaximumWidth(initial_width)
        self.tree_widget.setMinimumHeight(initial_height)
        self.tree_widget.setMaximumHeight(initial_height)

        # Connect expand/collapse signals to update indicators
        self.tree_widget.itemExpanded.connect(self._on_item_expanded)
        self.tree_widget.itemCollapsed.connect(self._on_item_collapsed)
        # Connect click signal to toggle expansion
        self.tree_widget.itemClicked.connect(self._on_item_clicked)

        layout.addWidget(self.tree_widget)

        # Set container size for both width and height
        container.setFixedWidth(initial_width + 10)
        container.setFixedHeight(initial_height + 10)

        # Add the widget to the graphics scene via proxy
        self.tree_proxy = QGraphicsProxyWidget(self.graphics)
        self.tree_proxy.setWidget(container)
        self.tree_proxy.setPos(10, 50)
        self.tree_proxy.setVisible(False)

        # Ensure the proxy widget is on top
        self.tree_proxy.setZValue(1)

    def _on_item_clicked(self, item, column):
        """Toggle expansion when an item with children is clicked."""
        if item.childCount() > 0:  # Only toggle if item has children
            if item.isExpanded():
                item.setExpanded(False)
            else:
                item.setExpanded(True)

    def _on_item_expanded(self, item):
        """Update item text when expanded."""
        text = item.text(0)
        if text.startswith("▶ "):
            item.setText(0, text.replace("▶ ", "▼ "))

    def _on_item_collapsed(self, item):
        """Update item text when collapsed."""
        text = item.text(0)
        if text.startswith("▼ "):
            item.setText(0, text.replace("▼ ", "▶ "))

    def _add_dict_items(self, parent_item, data, key=None):
        """Recursively add dictionary items to the tree."""
        if isinstance(data, dict):
            if key is not None:
                # Create a parent node for this dictionary
                item = QTreeWidgetItem(parent_item)
                item.setText(0, f"▶ {key}: {{{len(data)} items}}")
                item.setExpanded(False)
            else:
                item = parent_item

            # Add all key-value pairs
            for k, v in data.items():
                if isinstance(v, dict):
                    self._add_dict_items(item, v, k)
                elif isinstance(v, (list, tuple)):
                    self._add_list_items(item, v, k)
                else:
                    child = QTreeWidgetItem(item)
                    child.setText(0, f"{k}: {self._format_value(v)}")

        else:
            # Leaf node
            item = QTreeWidgetItem(parent_item)
            if key is not None:
                item.setText(0, f"{key}: {self._format_value(data)}")
            else:
                item.setText(0, self._format_value(data))

    def _add_list_items(self, parent_item, data, key=None):
        """Add list/tuple items to the tree."""
        type_name = "list" if isinstance(data, list) else "tuple"

        if key is not None:
            # Nested list/tuple - create a parent node
            item = QTreeWidgetItem(parent_item)
            item.setText(0, f"▶ {key}: {type_name}[{len(data)} items]")
            item.setExpanded(False)
        else:
            # Top-level list/tuple - create a parent node with type indicator
            item = QTreeWidgetItem(parent_item)
            item.setText(0, f"▶ {type_name}[{len(data)} items]")
            item.setExpanded(False)

        for idx, value in enumerate(data):
            if isinstance(value, dict):
                self._add_dict_items(item, value, f"[{idx}]")
            elif isinstance(value, (list, tuple)):
                self._add_list_items(item, value, f"[{idx}]")
            else:
                child = QTreeWidgetItem(item)
                child.setText(0, f"[{idx}]: {self._format_value(value)}")

    def _format_value(self, value):
        """Format a value for display."""
        if value is None:
            return "None"
        elif isinstance(value, bool):
            return str(value)
        elif isinstance(value, (int, float)):
            if isinstance(value, float):
                return f"{value:.4g}"
            return str(value)
        elif isinstance(value, str):
            # Truncate long strings
            if len(value) > 50:
                return f'"{value[:47]}..."'
            return f'"{value}"'
        else:
            s = str(value)
            if len(s) > 50:
                return f"{s[:47]}..."
            return s

    def _show_tree_view(self, value):
        """Show the tree view for dictionaries, lists, and tuples."""
        self._create_tree_widget()

        # Clear existing items
        self.tree_widget.clear()

        root = self.tree_widget.invisibleRootItem()

        # Populate the tree based on value type
        if isinstance(value, (list, tuple)):
            # For lists/tuples, add items directly to root
            self._add_list_items(root, value)
        elif isinstance(value, dict):
            # For dictionaries, use existing dict logic
            self._add_dict_items(root, value)
        else:
            # Fallback: wrap in a dict-like structure
            self._add_dict_items(root, {"result": value})

        # Expand the first level and update indicators
        for i in range(root.childCount()):
            child = root.child(i)
            if child.childCount() > 0:  # Only expand if it has children
                child.setExpanded(True)
                # Update the indicator
                text = child.text(0)
                if text.startswith("▶ "):
                    child.setText(0, text.replace("▶ ", "▼ "))

        # Ensure the node has a reasonable minimum height for tree view
        if self.graphics.height < 200:
            self.graphics.height = 200
            self.graphics.setRect(0, 0, self.graphics.width, self.graphics.height)

        # Update content sizes to fit current node dimensions
        self._update_content_sizes()

        # Show tree, hide text and image
        self.tree_proxy.setVisible(True)
        self.display_text.setVisible(False)
        if self.image_proxy is not None:
            self.image_proxy.setVisible(False)
        self.is_showing_tree = True
        self.is_showing_image = False

    def _create_image_widget(self):
        """Create the image label for displaying PIL images."""
        if self.image_label is not None:
            return

        # Create a container widget
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border: 1px solid #555;
                border-radius: 4px;
            }
            QLabel {
                background-color: #2b2b2b;
                border: none;
            }
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setAlignment(Qt.AlignCenter)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(False)

        # Initial sizes - will be updated dynamically on resize
        initial_width = max(100, self.graphics.width - 30)
        initial_height = max(80, self.graphics.height - 70)
        self.image_label.setMinimumWidth(initial_width)
        self.image_label.setMaximumWidth(initial_width)
        self.image_label.setMinimumHeight(initial_height)
        self.image_label.setMaximumHeight(initial_height)

        layout.addWidget(self.image_label)

        # Set container size
        container.setFixedWidth(initial_width + 10)
        container.setFixedHeight(initial_height + 10)

        # Add the widget to the graphics scene via proxy
        self.image_proxy = QGraphicsProxyWidget(self.graphics)
        self.image_proxy.setWidget(container)
        self.image_proxy.setPos(10, 50)
        self.image_proxy.setVisible(False)

        # Ensure the proxy widget is on top
        self.image_proxy.setZValue(1)

    def _show_image_view(self, image):
        """Show the image view for PIL.Image.Image objects."""
        self._create_image_widget()

        # Convert PIL Image to QPixmap
        if image.mode == "RGB":
            b, g, r = image.split()
            image = Image.merge("RGB", (b, g, r))
        elif image.mode == "RGBA":
            b, g, r, a = image.split()
            image = Image.merge("RGBA", (b, g, r, a))

        # Convert to bytes
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        # Create QPixmap
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.read())

        # Store the original pixmap for resizing
        self._current_pixmap = pixmap

        # Scale the image to fit within the label
        available_width = max(100, self.graphics.width - 30)
        available_height = max(80, self.graphics.height - 70)
        scaled_pixmap = pixmap.scaled(
            available_width,
            available_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.image_label.setPixmap(scaled_pixmap)

        # Ensure the node has a reasonable minimum size for image view
        if self.graphics.height < 250:
            self.graphics.height = 250
            self.graphics.setRect(0, 0, self.graphics.width, self.graphics.height)

        if self.graphics.width < 250:
            self.graphics.width = 250
            self.graphics.setRect(0, 0, self.graphics.width, self.graphics.height)

        # Update content sizes to fit current node dimensions
        self._update_content_sizes()

        # Show image, hide text and tree
        self.image_proxy.setVisible(True)
        self.display_text.setVisible(False)
        if self.tree_proxy is not None:
            self.tree_proxy.setVisible(False)

        self.is_showing_image = True
        self.is_showing_tree = False

    def _show_text_view(self, display_str):
        """Show the simple text view."""
        self.display_text.setPlainText(display_str)
        self.display_text.setVisible(True)

        if self.tree_proxy is not None:
            self.tree_proxy.setVisible(False)

        if self.image_proxy is not None:
            self.image_proxy.setVisible(False)

        # Ensure node has minimum height for text view
        min_height = 100 + max(len(self.inputs), len(self.outputs)) * 30
        if self.graphics.height < min_height:
            self.graphics.height = min_height
            self.graphics.setRect(0, 0, self.graphics.width, self.graphics.height)

        # Update content sizes to fit current node dimensions
        self._update_content_sizes()

        self.is_showing_tree = False
        self.is_showing_image = False

    def _deserialize_image(self, value: dict) -> Image.Image:
        """Deserialize a base64 encoded image dict back to PIL.Image.

        Args:
            value: Dictionary with __type__, data, and metadata

        Returns:
            PIL.Image object or None if deserialization fails
        """
        try:
            import base64

            # Decode base64 data
            image_data = base64.b64decode(value["data"])

            # Create PIL Image from bytes
            image = Image.open(BytesIO(image_data))
            return image
        except Exception as e:
            print(f"Error deserializing image: {e}")
            return None

    def set_value(self, value: Any):
        """Set and display a value (used by backend execution results).

        Args:
            value: The value to display
        """
        # Check if value is a serialized image from backend
        if isinstance(value, dict) and value.get("__type__") == "PIL.Image":
            # Deserialize the image
            value = self._deserialize_image(value)

        # Check if the value is a PIL Image
        is_pil_image = isinstance(value, Image.Image)

        # Update display only if value changed or showing different view type
        is_dict = isinstance(value, dict) and len(value) > 0
        is_list_or_tuple = isinstance(value, (list, tuple)) and len(value) > 0
        should_show_tree = is_dict or is_list_or_tuple

        should_update = (
            (value != self.cached_value)
            or (should_show_tree and not self.is_showing_tree)
            or (not should_show_tree and self.is_showing_tree)
            or (is_pil_image and not self.is_showing_image)
            or (not is_pil_image and self.is_showing_image)
        )

        if should_update:
            self.cached_value = value

            if value is None:
                self._show_text_view("None")
            elif is_pil_image:
                # Show PIL Image in image view
                self._show_image_view(value)
            elif isinstance(value, dict) and len(value) > 0:
                # Show dictionary in tree view
                self._show_tree_view(value)
            elif isinstance(value, (list, tuple)) and len(value) > 0:
                # Show lists and tuples in tree view
                self._show_tree_view(value)
            else:
                # For empty lists/tuples or other simple values, wrap in dict
                if isinstance(value, (list, tuple)):
                    self._show_tree_view(value)
                else:
                    self._show_tree_view({"result": value})
                # # Show simple values in text view
                # if isinstance(value, float):
                #     display_str = f"{value:.4g}"
                # else:
                #     display_str = str(value)
                # self._show_text_view(display_str)

    def execute(self) -> Any:
        """Display input value."""
        value = self.get_input_value(0)
        self.set_value(value)
        return value

from io import BytesIO
from typing import Any

import requests
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGraphicsProxyWidget,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from psynapse.core.node import Node
from psynapse.core.socket_types import SocketDataType
from psynapse.nodes.object_node import ObjectNode
from psynapse.utils import pil_image_to_openai_string


class ImageNode(ObjectNode):
    """Node that loads an image from URL or file upload and outputs a PIL.Image.Image."""

    def __init__(self):
        # Call Node.__init__ directly to bypass ObjectNode initialization
        Node.__init__(
            self,
            title="Image",
            inputs=[],
            outputs=[("Image", SocketDataType.ANY)],
        )

        self.current_image = None
        self.current_mode = "URL"  # "URL" or "Upload"
        self.return_as = "PIL Image"  # "PIL Image", "OpenAI string", or "LLM Content"
        self.image_url = ""
        self.image_path = ""

        # Create container widget
        self.widget_container = QWidget()
        self.widget_layout = QVBoxLayout()
        self.widget_layout.setContentsMargins(0, 0, 0, 0)
        self.widget_layout.setSpacing(8)
        self.widget_layout.setAlignment(Qt.AlignCenter)
        self.widget_container.setLayout(self.widget_layout)

        # Create mode selector
        self.mode_selector = QComboBox()
        self.mode_selector.addItem("URL", "URL")
        self.mode_selector.addItem("Upload", "Upload")
        self.mode_selector.setFixedWidth(160)
        self.mode_selector.currentIndexChanged.connect(self._on_mode_changed)

        # Style the mode selector
        self.mode_selector.setStyleSheet("""
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

        self.widget_layout.addWidget(self.mode_selector)

        # Create return format selector
        self.return_as_selector = QComboBox()
        self.return_as_selector.addItem("PIL Image", "PIL Image")
        self.return_as_selector.addItem("OpenAI string", "OpenAI string")
        self.return_as_selector.addItem("LLM Content", "LLM Content")
        self.return_as_selector.setFixedWidth(160)
        self.return_as_selector.currentIndexChanged.connect(self._on_return_as_changed)

        # Style the return as selector (same as mode selector)
        self.return_as_selector.setStyleSheet("""
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

        self.widget_layout.addWidget(self.return_as_selector)

        # Placeholder for input widget
        self.input_widget = None
        self._create_input_widget()

        # Add widget to graphics and center it
        self.widget_proxy = QGraphicsProxyWidget(self.graphics)
        self.widget_proxy.setWidget(self.widget_container)
        # Set high z-value to ensure dropdown appears above other elements
        self.widget_proxy.setZValue(200)

        # Update node height to accommodate widgets
        self.graphics.height = 190
        self.graphics.setRect(0, 0, self.graphics.width, self.graphics.height)

        # Update widget sizes and positions
        self._update_widget_sizes()

        # Override the graphics mouseMoveEvent to handle widget resizing
        self._original_mouse_move = self.graphics.mouseMoveEvent
        self.graphics.mouseMoveEvent = self._on_graphics_mouse_move

    def _on_mode_changed(self, index: int):
        """Handle mode selector change."""
        self.current_mode = self.mode_selector.itemData(index)
        self._create_input_widget()

    def _on_return_as_changed(self, index: int):
        """Handle return format selector change."""
        self.return_as = self.return_as_selector.itemData(index)
        # Clear output socket value to force re-execution with new format
        if self.output_sockets:
            self.output_sockets[0].value = None

    def _create_input_widget(self):
        """Create appropriate input widget based on selected mode."""
        # Remove old input widget if exists
        if self.input_widget:
            self.widget_layout.removeWidget(self.input_widget)
            self.input_widget.deleteLater()
            self.input_widget = None

        # Create new input widget based on mode
        if self.current_mode == "URL":
            self.input_widget = self._create_url_widget()
        elif self.current_mode == "Upload":
            self.input_widget = self._create_upload_widget()

        if self.input_widget:
            self.widget_layout.addWidget(self.input_widget)

    def _create_url_widget(self):
        """Create URL input widget."""
        widget = QLineEdit()
        widget.setPlaceholderText("Enter image URL...")
        widget.setFixedWidth(160)
        widget.setAlignment(Qt.AlignCenter)
        widget.setText(self.image_url)
        widget.textChanged.connect(self._on_url_changed)

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

    def _create_upload_widget(self):
        """Create file upload widget."""
        container = QWidget()
        container.setFixedWidth(160)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Upload button
        upload_btn = QPushButton("Choose File")
        upload_btn.setFixedWidth(160)
        upload_btn.clicked.connect(self._on_upload_clicked)

        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 3px;
                padding: 5px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #FF7700;
                border: 1px solid #FF7700;
            }
            QPushButton:pressed {
                background-color: #CC5500;
            }
        """)

        layout.addWidget(upload_btn)

        # File path display
        self.file_path_label = QLineEdit()
        self.file_path_label.setReadOnly(True)
        self.file_path_label.setPlaceholderText("No file selected")
        self.file_path_label.setFixedWidth(160)
        self.file_path_label.setAlignment(Qt.AlignCenter)
        if self.image_path:
            # Show just the filename
            import os

            self.file_path_label.setText(os.path.basename(self.image_path))

        self.file_path_label.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                color: #888888;
                border: 1px solid #444444;
                border-radius: 3px;
                padding: 5px 8px;
                font-size: 10px;
            }
        """)

        layout.addWidget(self.file_path_label)

        return container

    def _on_url_changed(self, text: str):
        """Handle URL text change."""
        self.image_url = text
        # Clear the current image when URL changes
        self.current_image = None
        if self.output_sockets:
            self.output_sockets[0].value = None

    def _on_upload_clicked(self):
        """Handle file upload button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;All Files (*)",
        )

        if file_path:
            self.image_path = file_path
            # Update the file path label
            import os

            self.file_path_label.setText(os.path.basename(file_path))
            # Clear the current image to force reload
            self.current_image = None
            if self.output_sockets:
                self.output_sockets[0].value = None

    def execute(self) -> Any:
        """Load and return the image in the selected format."""
        try:
            # Load the image first
            if self.current_mode == "URL":
                if not self.image_url:
                    return None

                # Load image from URL
                response = requests.get(self.image_url, timeout=10)
                response.raise_for_status()
                self.current_image = Image.open(BytesIO(response.content))

            elif self.current_mode == "Upload":
                if not self.image_path:
                    return None

                # Load image from file
                self.current_image = Image.open(self.image_path)

            # Return in the selected format
            if self.return_as == "PIL Image":
                return self.current_image
            elif self.return_as == "OpenAI string":
                return pil_image_to_openai_string(self.current_image)
            elif self.return_as == "LLM Content":
                return {
                    "type": "input_image",
                    "image_url": pil_image_to_openai_string(self.current_image),
                }
            else:
                return self.current_image

        except Exception as e:
            print(f"Error loading image: {e}")
            return None

    def _on_graphics_mouse_move(self, event):
        """Handle mouse move on graphics item, updating widget sizes when resizing."""
        # Call original mouseMoveEvent
        self._original_mouse_move(event)

        # If we're resizing, update widget sizes
        if self.graphics.is_resizing:
            self._update_widget_sizes()

    def _update_widget_sizes(self):
        """Update the sizes of widgets to fit the current node size."""
        # Calculate available width (leave margins on both sides)
        left_margin = 10
        right_margin = 10
        available_width = max(80, self.graphics.width - left_margin - right_margin)

        # Update container width
        self.widget_container.setFixedWidth(available_width)

        # Update mode selector width
        self.mode_selector.setFixedWidth(available_width)

        # Update return as selector width
        self.return_as_selector.setFixedWidth(available_width)

        # Update input widget width
        if self.input_widget:
            self.input_widget.setFixedWidth(available_width)

            # If it's the upload widget, also update its children
            if self.current_mode == "Upload":
                for child in self.input_widget.findChildren(QPushButton):
                    child.setFixedWidth(available_width)
                for child in self.input_widget.findChildren(QLineEdit):
                    child.setFixedWidth(available_width)

        # Center the widget container horizontally in the node
        widget_x = (self.graphics.width - available_width) / 2
        self.widget_proxy.setPos(widget_x, 40)

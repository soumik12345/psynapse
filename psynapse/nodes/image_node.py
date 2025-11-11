from io import BytesIO
from typing import Any

import requests
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGraphicsProxyWidget,
    QLabel,
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

        # Create label for input mode selector
        self.input_mode_label = QLabel("Input Mode")
        self.input_mode_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 10px;
                padding: 2px 0px;
            }
        """)
        self.input_mode_label.setAlignment(Qt.AlignCenter)
        self.widget_layout.addWidget(self.input_mode_label)

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

        # Create label for output mode selector
        self.output_mode_label = QLabel("Output Mode")
        self.output_mode_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 10px;
                padding: 2px 0px;
            }
        """)
        self.output_mode_label.setAlignment(Qt.AlignCenter)
        self.widget_layout.addWidget(self.output_mode_label)

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

        # Create image preview label
        self.image_preview_label = QLabel()
        self.image_preview_label.setFixedWidth(160)
        self.image_preview_label.setFixedHeight(120)
        self.image_preview_label.setAlignment(Qt.AlignCenter)
        self.image_preview_label.setText("No image")
        self.image_preview_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                color: #888888;
                border: 1px solid #444444;
                border-radius: 3px;
                font-size: 10px;
            }
        """)
        self.widget_layout.addWidget(self.image_preview_label)

        # Placeholder for input widget
        self.input_widget = None
        self._create_input_widget()

        # Add widget to graphics and center it
        self.widget_proxy = QGraphicsProxyWidget(self.graphics)
        self.widget_proxy.setWidget(self.widget_container)
        # Set high z-value to ensure dropdown appears above other elements
        self.widget_proxy.setZValue(200)

        # Update node height to accommodate widgets
        # Height calculation:
        # - Title bar: ~30px
        # - Widget container starts at: ~40px
        # - "Input Mode" label: ~15px
        # - Mode selector: ~30px
        # - "Output Mode" label: ~15px
        # - Return format selector: ~30px
        # - Image preview: ~120px
        # - Input widget (worst case Upload): ~60px
        # - Spacing between elements: ~48px total
        # - Bottom padding: ~10px
        # Total: ~358px, rounded to 360px
        self.graphics.height = 360
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
        # Reload preview if we have a URL or path
        if (self.current_mode == "URL" and self.image_url) or (
            self.current_mode == "Upload" and self.image_path
        ):
            self._load_and_preview_image()
        else:
            self._clear_preview()

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
        # Load and preview the image if URL is provided
        if text:
            self._load_and_preview_image()

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
            # Load and preview the image
            self._load_and_preview_image()

    def _load_and_preview_image(self):
        """Load image from URL or file and display preview without executing the node."""
        try:
            image = None

            if self.current_mode == "URL":
                if not self.image_url:
                    self._clear_preview()
                    return

                # Load image from URL
                response = requests.get(self.image_url, timeout=10)
                response.raise_for_status()
                image = Image.open(BytesIO(response.content))

            elif self.current_mode == "Upload":
                if not self.image_path:
                    self._clear_preview()
                    return

                # Load image from file
                image = Image.open(self.image_path)

            if image:
                self.current_image = image
                self._update_preview(image)
            else:
                self._clear_preview()

        except Exception as e:
            print(f"Error loading image preview: {e}")
            self._clear_preview()

    def _update_preview(self, image: Image.Image):
        """Update the preview label with the given PIL Image."""
        try:
            # Convert PIL Image to QPixmap
            # Handle color mode conversion for Qt compatibility (matching ViewNode)
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

            # Scale the image to fit the preview label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.image_preview_label.width(),
                self.image_preview_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )

            self.image_preview_label.setPixmap(scaled_pixmap)

        except Exception as e:
            print(f"Error updating preview: {e}")
            self._clear_preview()

    def _clear_preview(self):
        """Clear the image preview."""
        self.image_preview_label.clear()
        self.image_preview_label.setText("No image")
        self.current_image = None

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

        # Update label widths
        self.input_mode_label.setFixedWidth(available_width)
        self.output_mode_label.setFixedWidth(available_width)

        # Update mode selector width
        self.mode_selector.setFixedWidth(available_width)

        # Update return as selector width
        self.return_as_selector.setFixedWidth(available_width)

        # Update image preview width
        self.image_preview_label.setFixedWidth(available_width)

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

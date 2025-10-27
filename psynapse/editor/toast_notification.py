from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class ToastNotification(QFrame):
    """A toast notification widget that displays at the bottom-right of the window."""

    def __init__(
        self, message: str, node_title: str = None, on_close_callback=None, parent=None
    ):
        super().__init__(parent)
        self.message = message
        self.node_title = node_title
        self.on_close_callback = on_close_callback

        self._setup_ui()
        # Make it stay on top of other widgets but within the parent window
        self.setAutoFillBackground(True)
        self.raise_()

    def _setup_ui(self):
        """Set up the toast UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        # Header layout with title and close button
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Error title
        if self.node_title:
            title_text = f"Error in {self.node_title}"
        else:
            title_text = "Node Execution Error"

        title_label = QLabel(title_text)
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ff4444;")
        header_layout.addWidget(title_label, 1)

        # Close button
        close_button = QPushButton("✕")
        close_button.setFixedSize(24, 24)
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.clicked.connect(self.close_toast)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ffffff;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        header_layout.addWidget(close_button)

        main_layout.addLayout(header_layout)

        # Error message
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setMaximumWidth(350)
        message_font = QFont()
        message_font.setPointSize(10)
        message_label.setFont(message_font)
        message_label.setStyleSheet("color: #cccccc;")
        main_layout.addWidget(message_label)

        # Style the toast with solid background
        self.setStyleSheet("""
            ToastNotification {
                background-color: #2d2d2d;
                border: 2px solid #ff4444;
                border-radius: 8px;
            }
        """)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)

        # Set minimum size
        self.setMinimumWidth(300)
        self.setMaximumWidth(400)

    def close_toast(self):
        """Close this toast notification."""
        # Hide immediately for instant visual feedback
        self.hide()

        # Find and notify the toast manager
        parent = self.parent()
        if parent and hasattr(parent, "toast_manager"):
            parent.toast_manager._remove_toast(self)

        # Call the close callback if provided (after removing from manager)
        if self.on_close_callback:
            self.on_close_callback()

        # Schedule deletion
        self.deleteLater()


class ToastManager:
    """Manages multiple toast notifications."""

    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.toasts = []
        self.toast_spacing = 10
        self.bottom_margin = 20
        self.right_margin = 20

    def show_error(self, message: str, node_title: str = None, on_close=None):
        """Show an error toast notification."""
        toast = ToastNotification(message, node_title, on_close, self.parent_window)
        self.toasts.append(toast)
        self._reposition_toasts()
        toast.show()

    def _remove_toast(self, toast: ToastNotification):
        """Remove a toast from the list and reposition remaining toasts."""
        if toast in self.toasts:
            self.toasts.remove(toast)
            self._reposition_toasts()

    def _reposition_toasts(self):
        """Reposition all toasts in a stack at the bottom-right."""
        if not self.parent_window:
            return

        # Get the parent window's size
        parent_width = self.parent_window.width()
        parent_height = self.parent_window.height()

        # Account for status bar height
        status_bar_height = 0
        if hasattr(self.parent_window, "statusBar") and self.parent_window.statusBar():
            status_bar_height = self.parent_window.statusBar().height()

        y_position = parent_height - self.bottom_margin - status_bar_height

        # Position toasts from bottom to top
        for toast in reversed(self.toasts):
            # Ensure toast is properly sized
            toast.adjustSize()
            toast_height = toast.height()
            toast_width = toast.width()

            x_position = parent_width - toast_width - self.right_margin
            y_position -= toast_height

            toast.move(x_position, y_position)
            toast.raise_()

            y_position -= self.toast_spacing

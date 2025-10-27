"""Toast notification widget for error messages."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
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
        self.setWindowFlags(
            Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)

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

        # Style the toast
        self.setStyleSheet("""
            ToastNotification {
                background-color: #2d2d2d;
                border: 2px solid #ff4444;
                border-radius: 8px;
            }
        """)

        # Set minimum size
        self.setMinimumWidth(300)
        self.setMaximumWidth(400)

    def close_toast(self):
        """Close this toast notification."""
        # Call the close callback if provided
        if self.on_close_callback:
            self.on_close_callback()

        if self.parent():
            # Remove from parent's toast list
            parent = self.parent()
            if hasattr(parent, "_remove_toast"):
                parent._remove_toast(self)
        self.deleteLater()


class ToastManager(QWidget):
    """Manages multiple toast notifications."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.toasts = []
        self.toast_spacing = 10
        self.bottom_margin = 20
        self.right_margin = 20

        # Make this widget transparent and not blocking
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

    def show_error(self, message: str, node_title: str = None, on_close=None):
        """Show an error toast notification."""
        toast = ToastNotification(message, node_title, on_close, self.parent())
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
        if not self.parent():
            return

        parent_rect = self.parent().rect()
        y_position = parent_rect.height() - self.bottom_margin

        # Position toasts from bottom to top
        for toast in reversed(self.toasts):
            toast_height = toast.sizeHint().height()
            toast_width = toast.sizeHint().width()

            x_position = parent_rect.width() - toast_width - self.right_margin
            y_position -= toast_height

            toast.move(x_position, y_position)
            toast.raise_()

            y_position -= self.toast_spacing

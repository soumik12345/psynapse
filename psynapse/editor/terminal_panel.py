"""Terminal panel widget for displaying backend output."""

import sys
import threading

from PySide6.QtCore import QProcess, QProcessEnvironment, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QTextCharFormat
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class TerminalPanel(QWidget):
    """Collapsible terminal panel for displaying backend process output."""

    # Signal emitted when backend is ready
    backend_ready = Signal()
    # Signal emitted when a log message is received from SSE
    log_received = Signal(str)

    def __init__(self, parent=None, backend_port=None):
        """Initialize the terminal panel.

        Args:
            parent: Parent widget
            backend_port: Optional port number of existing backend to connect to.
                         If None, a new backend will be spawned.
        """
        super().__init__(parent)
        self.parent = parent
        self.is_collapsed = False
        self.backend_process = None
        self.backend_ready_emitted = False
        self.health_check_timer = None
        self.backend_port = backend_port or 8000
        self.use_existing_backend = backend_port is not None
        self.sse_thread = None
        self.sse_stop_event = threading.Event()

        # Connect signal for thread-safe log display
        self.log_received.connect(self._display_log_message)

        self._setup_ui()
        if self.use_existing_backend:
            self._connect_to_existing_backend()
        else:
            self._start_backend()

    def _setup_ui(self):
        """Set up the UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with collapse button
        header = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 5, 10, 5)

        self.title_label = QLabel("Backend Terminal")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 12px;")

        self.collapse_button = QPushButton("▼")
        self.collapse_button.setFixedSize(20, 20)
        self.collapse_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-radius: 3px;
            }
        """)
        self.collapse_button.clicked.connect(self._toggle_collapse)

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.collapse_button)
        header.setLayout(header_layout)
        header.setStyleSheet(
            "background-color: #f0f0f0; border-bottom: 1px solid #d0d0d0;"
        )

        # Terminal output area
        self.terminal_output = QPlainTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setFont(
            QFont("Monaco", 10) if sys.platform == "darwin" else QFont("Consolas", 10)
        )
        self.terminal_output.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
            }
        """)
        # Set dark theme colors
        palette = self.terminal_output.palette()
        palette.setColor(palette.ColorRole.Base, QColor("#1e1e1e"))
        palette.setColor(palette.ColorRole.Text, QColor("#d4d4d4"))
        self.terminal_output.setPalette(palette)

        layout.addWidget(header)
        layout.addWidget(self.terminal_output)

        self.setLayout(layout)
        self.setMinimumWidth(300)
        self.setMaximumWidth(600)

    def _toggle_collapse(self):
        """Toggle collapse/expand state."""
        self.is_collapsed = not self.is_collapsed
        if self.is_collapsed:
            self.collapse_button.setText("▶")
            self.terminal_output.hide()
            self.setMaximumWidth(200)
            self.setMinimumWidth(200)
        else:
            self.collapse_button.setText("▼")
            self.terminal_output.show()
            self.setMaximumWidth(600)
            self.setMinimumWidth(300)

    def _start_backend(self):
        """Start the backend process."""
        self._append_output("Starting backend server...\n", QColor("#4CAF50"))

        # Create QProcess to run backend
        self.backend_process = QProcess(self)
        self.backend_process.readyReadStandardOutput.connect(self._on_stdout)
        self.backend_process.readyReadStandardError.connect(self._on_stderr)
        self.backend_process.finished.connect(self._on_process_finished)
        self.backend_process.stateChanged.connect(self._on_process_state_changed)

        # Set up environment
        env = QProcessEnvironment.systemEnvironment()
        self.backend_process.setProcessEnvironment(env)

        # Start the backend process
        # Use 'uv run' to execute uvicorn
        command = "uv"
        args = [
            "run",
            "uvicorn",
            "psynapse.backend.server:app",
            "--reload",
            "--host",
            "0.0.0.0",
        ]

        self.backend_process.start(command, args)

        if not self.backend_process.waitForStarted(5000):
            error_msg = (
                f"Failed to start backend: {self.backend_process.errorString()}\n"
            )
            self._append_output(error_msg, QColor("#f44336"))

    def _on_stdout(self):
        """Handle stdout output from backend process."""
        data = (
            self.backend_process.readAllStandardOutput()
            .data()
            .decode("utf-8", errors="replace")
        )
        if data:
            self._append_output(data, QColor("#d4d4d4"))
            # Check if backend is ready by looking for uvicorn startup message
            if not self.backend_ready_emitted:
                if (
                    "Uvicorn running on" in data
                    or "Application startup complete" in data
                ):
                    self._mark_backend_ready()

    def _on_stderr(self):
        """Handle stderr output from backend process."""
        data = (
            self.backend_process.readAllStandardError()
            .data()
            .decode("utf-8", errors="replace")
        )
        if data:
            self._append_output(data, QColor("#ff9800"))

    def _on_process_finished(self, exit_code, exit_status):
        """Handle process finished event."""
        if exit_code != 0:
            self._append_output(
                f"\nBackend process exited with code {exit_code}\n", QColor("#f44336")
            )
        else:
            self._append_output("\nBackend process stopped.\n", QColor("#4CAF50"))

    def _on_process_state_changed(self, state):
        """Handle process state changes."""
        if state == QProcess.ProcessState.Running:
            self.title_label.setText("Backend Terminal (Starting...)")
            self.title_label.setStyleSheet(
                "font-weight: bold; font-size: 12px; color: #ff9800;"
            )
            # Start periodic health check to detect when backend is ready
            if not self.backend_ready_emitted:
                self._start_health_check()
        elif state == QProcess.ProcessState.NotRunning:
            self.title_label.setText("Backend Terminal (Stopped)")
            self.title_label.setStyleSheet(
                "font-weight: bold; font-size: 12px; color: #f44336;"
            )
            self._stop_health_check()
            self.backend_ready_emitted = False

    def _start_health_check(self):
        """Start periodic health check to detect when backend is ready."""
        if self.health_check_timer is None:
            self.health_check_timer = QTimer(self)
            self.health_check_timer.timeout.connect(self._check_backend_health)
            self.health_check_timer.start(500)  # Check every 500ms

    def _stop_health_check(self):
        """Stop the health check timer."""
        if self.health_check_timer:
            self.health_check_timer.stop()
            self.health_check_timer = None

    def _check_backend_health(self):
        """Check if backend health endpoint is responding."""
        if self.backend_ready_emitted:
            self._stop_health_check()
            return

        # Use synchronous health check (avoiding async complexity here)
        try:
            import urllib.error
            import urllib.request

            url = f"http://localhost:{self.backend_port}/health"
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "Psynapse-Editor")
            with urllib.request.urlopen(req, timeout=0.5) as response:
                if response.status == 200:
                    self._mark_backend_ready()
        except Exception:
            # Backend not ready yet, continue checking
            pass

    def _connect_to_existing_backend(self):
        """Connect to an existing backend running on the specified port."""
        self._append_output(
            f"Connecting to existing backend on port {self.backend_port}...\n",
            QColor("#4CAF50"),
        )
        self.title_label.setText("Backend Terminal (Connecting...)")
        self.title_label.setStyleSheet(
            "font-weight: bold; font-size: 12px; color: #ff9800;"
        )

        # Start health check to verify backend is available
        self._start_health_check()

        # Start SSE log streaming in a separate thread
        self._start_sse_log_stream()

    def _start_sse_log_stream(self):
        """Start SSE log streaming in a background thread."""
        self._append_output(
            "Starting log stream from backend...\n",
            QColor("#d4d4d4"),
        )

        def sse_worker():
            """Worker function to receive SSE log messages."""
            import urllib.error
            import urllib.request

            url = f"http://localhost:{self.backend_port}/logs"
            try:
                req = urllib.request.Request(url)
                req.add_header("Accept", "text/event-stream")
                req.add_header("User-Agent", "Psynapse-Editor")

                with urllib.request.urlopen(req, timeout=None) as response:
                    # Read SSE stream line by line
                    for line in response:
                        if self.sse_stop_event.is_set():
                            break

                        line_str = line.decode("utf-8").strip()
                        if line_str.startswith("data: "):
                            # Extract log message from SSE data field
                            log_msg = line_str[6:]  # Remove "data: " prefix
                            self.log_received.emit(log_msg)

            except Exception as e:
                if not self.sse_stop_event.is_set():
                    # Only show error if we didn't intentionally stop
                    self.log_received.emit(
                        f"[SSE Error] Failed to connect to log stream: {str(e)}"
                    )

        self.sse_stop_event.clear()
        self.sse_thread = threading.Thread(target=sse_worker, daemon=True)
        self.sse_thread.start()

    def _display_log_message(self, message: str):
        """Display a log message received from SSE stream.

        This method is called from the Qt main thread via signal/slot.

        Args:
            message: Log message to display
        """
        # Determine color based on log level
        color = QColor("#d4d4d4")  # Default white-ish
        if "[SSE Error]" in message or "ERROR" in message or "Error" in message:
            color = QColor("#f44336")  # Red
        elif "WARNING" in message or "Warning" in message:
            color = QColor("#ff9800")  # Orange
        elif "INFO" in message or "✓" in message:
            color = QColor("#4CAF50")  # Green

        self._append_output(message + "\n", color)

    def _mark_backend_ready(self):
        """Mark backend as ready and emit signal."""
        if not self.backend_ready_emitted:
            self.backend_ready_emitted = True
            if self.use_existing_backend:
                self.title_label.setText(
                    f"Backend Terminal (Connected - Port {self.backend_port})"
                )
                self._append_output(
                    f"✓ Successfully connected to backend on port {self.backend_port}\n",
                    QColor("#4CAF50"),
                )
            else:
                self.title_label.setText("Backend Terminal (Running)")
            self.title_label.setStyleSheet(
                "font-weight: bold; font-size: 12px; color: #4CAF50;"
            )
            self._stop_health_check()
            self.backend_ready.emit()

    def _append_output(self, text, color=None):
        """Append text to terminal output with optional color.

        Args:
            text: Text to append
            color: Optional QColor for text color
        """
        if color:
            char_format = QTextCharFormat()
            char_format.setForeground(color)
            cursor = self.terminal_output.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            cursor.setCharFormat(char_format)
            cursor.insertText(text)
            cursor.setCharFormat(QTextCharFormat())  # Reset format
        else:
            self.terminal_output.appendPlainText(text)

        # Auto-scroll to bottom
        scrollbar = self.terminal_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def stop_backend(self):
        """Stop the backend process (only if we spawned it)."""
        self._stop_health_check()

        # Stop SSE thread if running
        if self.sse_thread and self.sse_thread.is_alive():
            self.sse_stop_event.set()
            # Give thread a moment to stop gracefully
            self.sse_thread.join(timeout=1.0)

        if (
            not self.use_existing_backend
            and self.backend_process
            and self.backend_process.state() == QProcess.ProcessState.Running
        ):
            self._append_output("\nStopping backend server...\n", QColor("#ff9800"))
            self.backend_process.terminate()
            if not self.backend_process.waitForFinished(3000):
                self.backend_process.kill()
                self.backend_process.waitForFinished(3000)
        elif self.use_existing_backend:
            self._append_output(
                f"\nDisconnected from backend on port {self.backend_port}\n",
                QColor("#d4d4d4"),
            )
        self.backend_ready_emitted = False

    def closeEvent(self, event):
        """Handle close event - stop backend process."""
        self.stop_backend()
        super().closeEvent(event)

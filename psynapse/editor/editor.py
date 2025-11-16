import asyncio
import json

from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QFont, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QGraphicsTextItem,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from psynapse.core.edge import Edge
from psynapse.core.scene import NodeScene
from psynapse.core.serializer import GraphSerializer
from psynapse.core.socket_types import SocketDataType
from psynapse.core.view import NodeView
from psynapse.editor.backend_client import BackendClient
from psynapse.editor.node_library_panel import NodeLibraryPanel
from psynapse.editor.settings_dialog import SettingsDialog
from psynapse.editor.terminal_panel import TerminalPanel
from psynapse.editor.toast_notification import ToastManager
from psynapse.nodes.dictionary_node import DictionaryNode
from psynapse.nodes.image_node import ImageNode
from psynapse.nodes.list_node import ListNode
from psynapse.nodes.object_node import ObjectNode
from psynapse.nodes.ops import OpNode
from psynapse.nodes.pydantic_schema_node import PydanticSchemaNode
from psynapse.nodes.text_node import TextNode
from psynapse.nodes.view_node import ViewNode
from psynapse.utils import pretty_print_payload


class ExecutionWorker(QObject):
    """Worker object for running graph execution in a separate thread."""

    # Signals
    progress = Signal(str, str)  # node_id, node_type
    finished = Signal(dict)  # results
    error = Signal(str)  # error message

    def __init__(self, backend_client, graph_data, env_vars):
        """Initialize the worker.

        Args:
            backend_client: BackendClient instance
            graph_data: Serialized graph data
            env_vars: Environment variables dictionary
        """
        super().__init__()
        self.backend_client = backend_client
        self.graph_data = graph_data
        self.env_vars = env_vars

    def run(self):
        """Run the execution in the worker thread."""
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Run the async execution with progress streaming
                result = loop.run_until_complete(
                    self.backend_client.execute_graph_stream(
                        self.graph_data,
                        self.env_vars,
                        progress_callback=self._on_progress,
                    )
                )
                self.finished.emit(result)
            finally:
                loop.close()

        except Exception as e:
            self.error.emit(str(e))

    def _on_progress(self, node_id: str, node_type: str):
        """Handle progress updates from the backend.

        Args:
            node_id: ID of the node being executed
            node_type: Type of the node being executed
        """
        self.progress.emit(node_id, node_type)


class PsynapseEditor(QMainWindow):
    """Main node editor window."""

    def __init__(self, backend_port=None, timeout_keep_alive=3600):
        """Initialize the editor.

        Args:
            backend_port: Optional port number of existing backend to connect to.
                         If None, a new backend will be spawned.
            timeout_keep_alive: Timeout for keep-alive connections in spawned backend (seconds).
        """
        super().__init__()
        self.backend_port = backend_port or 8000
        self.timeout_keep_alive = timeout_keep_alive

        self.setWindowTitle("Psynapse")
        self.setGeometry(100, 100, 1200, 800)

        # Create scene and view
        self.scene = NodeScene()
        self.view = NodeView(self.scene, self)

        # Create node library panel
        self.node_library = NodeLibraryPanel(self)

        # Create Run button
        self.run_button = QPushButton("▶ Run Graph")
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.run_button.clicked.connect(self._run_graph)

        # Create container for view and run button
        view_container = QWidget()
        view_layout = QVBoxLayout()
        view_layout.addWidget(self.run_button)
        view_layout.addWidget(self.view)
        view_layout.setContentsMargins(5, 5, 5, 5)
        view_layout.setSpacing(5)
        view_container.setLayout(view_layout)

        # Create terminal panel for backend output
        self.terminal_panel = TerminalPanel(
            self, backend_port=backend_port, timeout_keep_alive=timeout_keep_alive
        )
        # Connect signal to load schemas when backend is ready
        self.terminal_panel.backend_ready.connect(self._load_node_schemas)

        # Create splitter to hold library, view, and terminal
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.node_library)
        splitter.addWidget(view_container)
        splitter.addWidget(self.terminal_panel)

        # Set initial sizes (library: 250px, view: rest, terminal: 400px)
        splitter.setSizes([250, 700, 400])
        splitter.setStretchFactor(0, 0)  # Don't stretch library
        splitter.setStretchFactor(1, 1)  # Stretch view
        splitter.setStretchFactor(2, 0)  # Don't stretch terminal

        self.setCentralWidget(splitter)

        # Track all nodes
        self.nodes = []
        self.view_nodes = []

        # Create toast manager for error notifications
        self.toast_manager = ToastManager(self)

        # Track current errors to prevent duplicates and stop execution
        self.current_errors = {}  # node_id -> error_message
        self.execution_paused = False

        # Set up error handler for nodes
        from psynapse.core.node import Node

        Node.error_handler = self._handle_node_error

        # Create menu bar
        self._create_menu_bar()

        # Backend client for graph execution
        base_url = f"http://localhost:{self.backend_port}"
        self.backend_client = BackendClient(base_url=base_url)

        # Execution thread and worker
        self.execution_thread = None
        self.execution_worker = None

        # NOTE: Removed auto-execution timer - graphs are now executed on-demand via Run button

        # Create timer to poll current node status
        self.current_node_timer = QTimer(self)
        self.current_node_timer.timeout.connect(self._update_current_node_status)
        self.current_node_timer.start(500)  # Poll every 500ms

        # Track currently executing node for visual feedback
        self._current_executing_node = None

        # Add welcome message
        self._add_welcome_message()

        # Note: Node schemas will be loaded automatically when backend is ready
        # via the backend_ready signal from terminal_panel

        # Node class mapping for drag-and-drop (get from library panel)
        self.node_class_map = self.node_library.get_node_class_map()

        # Add status bar to show execution state
        if backend_port is None:
            self.statusBar().showMessage("Ready - Starting backend...")
        else:
            self.statusBar().showMessage(
                f"Ready - Connecting to backend on port {backend_port}..."
            )

    def _create_menu_bar(self):
        """Create menu bar with node options."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._clear_scene)
        file_menu.addAction(new_action)

        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._open_graph)
        file_menu.addAction(open_action)

        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut("Ctrl+S")
        save_as_action.triggered.connect(self._save_as_graph)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        settings_action = QAction("&Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut(QKeySequence.ZoomIn)
        zoom_in_action.triggered.connect(self._zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut(QKeySequence.ZoomOut)
        zoom_out_action.triggered.connect(self._zoom_out)
        view_menu.addAction(zoom_out_action)

        reset_zoom_action = QAction("Reset Zoom", self)
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.triggered.connect(self._reset_zoom)
        view_menu.addAction(reset_zoom_action)

        view_menu.addSeparator()

        toggle_library_action = QAction("Toggle Node Library", self)
        toggle_library_action.setShortcut("Ctrl+B")
        toggle_library_action.triggered.connect(self._toggle_library_panel)
        view_menu.addAction(toggle_library_action)

        toggle_terminal_action = QAction("Toggle Terminal", self)
        toggle_terminal_action.setShortcut("Ctrl+`")
        toggle_terminal_action.triggered.connect(self._toggle_terminal_panel)
        view_menu.addAction(toggle_terminal_action)

    def _clear_all_executing_states(self):
        """Clear executing state from all nodes as a safeguard."""
        for node in self.nodes:
            if hasattr(node, "graphics"):
                node.graphics.set_executing_state(False)
        self._current_executing_node = None

    def _update_current_node_status(self):
        """Poll the backend for current node status and update the status bar and node visuals."""
        try:
            # Query backend for current node
            response = self.backend_client.get_current_node_sync()
            current_node = response.get("current_node")

            # Clear executing state from previously executing node
            if self._current_executing_node is not None:
                self._current_executing_node.graphics.set_executing_state(False)
                self._current_executing_node = None

            if current_node:
                node_id = current_node.get("node_id", "")
                node_type = current_node.get("node_type", "")

                # Extract node number from node_id (e.g., "node_0" -> "0")
                node_number = node_id.split("_")[-1] if "_" in node_id else node_id

                # Update status bar
                self.statusBar().showMessage(
                    f"⚙️ Executing Node {node_number} ({node_type})..."
                )

                # Find the node by ID and set executing state
                # First, ensure no other node has executing state (safeguard)
                for node in self.nodes:
                    if node != self._current_executing_node and hasattr(
                        node, "graphics"
                    ):
                        if node.graphics.is_executing:
                            node.graphics.set_executing_state(False)

                # Then set executing state on the current node
                try:
                    # Extract index from node_id (e.g., "node_0" -> 0)
                    if "_" in node_id:
                        node_index = int(node_id.split("_")[-1])
                        if 0 <= node_index < len(self.nodes):
                            executing_node = self.nodes[node_index]
                            executing_node.graphics.set_executing_state(True)
                            self._current_executing_node = executing_node
                except (ValueError, IndexError):
                    # Invalid node ID format or index out of range
                    pass
            else:
                # No node executing, ensure all nodes are cleared
                self._clear_all_executing_states()
                # Clear status bar
                if not self.execution_thread or not self.execution_thread.isRunning():
                    self.statusBar().showMessage("Ready")
        except Exception:
            # Silently ignore errors - the timer will retry on next tick
            pass

    def _load_node_schemas(self):
        """Load node schemas from the backend and populate the node library."""
        try:
            # Try to fetch schemas from backend
            response = self.backend_client.get_node_schemas_sync()
            # Backend returns {"nodes": [...]} not {"schemas": [...]}
            schemas = response.get("nodes", [])
            if schemas:
                self.node_library.load_schemas(schemas)
                # Update node class map after loading schemas so drag-and-drop works
                self.node_class_map = self.node_library.get_node_class_map()
                self.statusBar().showMessage(
                    f"✓ Loaded {len(schemas)} node types from backend"
                )
            else:
                self.statusBar().showMessage("⚠ No schemas received from backend")
        except Exception as e:
            # If backend is not available, continue without schemas
            # The operation nodes will not be available, but the app can still function
            self.statusBar().showMessage(
                f"⚠ Could not load node schemas from backend: {str(e)}"
            )

    def _clear_scene(self):
        """Clear all nodes from the scene."""
        # Clear executing state from all nodes before clearing
        self._clear_all_executing_states()

        self.scene.clear()
        self.nodes.clear()
        self.view_nodes.clear()
        self.welcome_text = None
        self._add_welcome_message()

    def _open_settings(self):
        """Open the settings dialog."""
        dialog = SettingsDialog(self)
        dialog.exec()

    def _open_graph(self):
        """Open a graph from a JSON file."""
        # Show file dialog for opening
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Graph", "", "JSON Files (*.json);;All Files (*)"
        )

        # If user canceled the dialog, return
        if not file_path:
            return

        try:
            # Load JSON file
            with open(file_path, "r") as f:
                graph_data = json.load(f)

            # Validate structure
            if not isinstance(graph_data, dict):
                raise ValueError("Invalid graph format: root must be a dictionary")

            if "nodes" not in graph_data or "edges" not in graph_data:
                raise ValueError("Invalid graph format: missing 'nodes' or 'edges' key")

            # Clear current scene
            self._clear_scene()

            # Load the graph
            self._load_graph_from_data(graph_data)

            # Update status bar
            self.statusBar().showMessage(f"✓ Graph loaded from {file_path}")

        except json.JSONDecodeError as e:
            self.toast_manager.show_error(
                f"Failed to parse JSON: {str(e)}", "Load Error"
            )
            self.statusBar().showMessage(f"❌ Invalid JSON file")
        except Exception as e:
            self.toast_manager.show_error(
                f"Failed to load graph: {str(e)}", "Load Error"
            )
            self.statusBar().showMessage(f"❌ Failed to load graph: {str(e)}")

    def _save_as_graph(self):
        """Save the current graph as a JSON file."""
        # Show file dialog for save location
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Graph As", "", "JSON Files (*.json);;All Files (*)"
        )

        # If user canceled the dialog, return
        if not file_path:
            return

        try:
            # Serialize the graph without output socket values for saving
            graph_data = GraphSerializer.serialize_graph(
                self.nodes, include_output_values=False
            )

            # Save to file
            with open(file_path, "w") as f:
                json.dump(graph_data, f, indent=2)

            # Update status bar
            self.statusBar().showMessage(f"✓ Graph saved to {file_path}")

        except Exception as e:
            # Show error toast
            self.toast_manager.show_error(
                f"Failed to save graph: {str(e)}", "Save Error"
            )
            self.statusBar().showMessage(f"❌ Failed to save graph: {str(e)}")

    def _zoom_in(self):
        """Zoom in the view."""
        self.view.scale(1.2, 1.2)

    def _zoom_out(self):
        """Zoom out the view."""
        self.view.scale(1 / 1.2, 1 / 1.2)

    def _reset_zoom(self):
        """Reset zoom to 100%."""
        self.view.resetTransform()
        self.view.zoom_factor = 1.0

    def _toggle_library_panel(self):
        """Toggle the visibility of the node library panel."""
        if self.node_library.isVisible():
            self.node_library.hide()
        else:
            self.node_library.show()

    def _toggle_terminal_panel(self):
        """Toggle the visibility of the terminal panel."""
        if self.terminal_panel.isVisible():
            self.terminal_panel.hide()
        else:
            self.terminal_panel.show()

    def _run_graph(self):
        """Execute the graph via the backend using a worker thread."""
        # Check if an execution is already running
        if self.execution_thread and self.execution_thread.isRunning():
            self.toast_manager.show_error(
                "Graph execution is already in progress. Please wait for it to complete.",
                "Execution In Progress",
            )
            return

        # Check if backend is available
        self.statusBar().showMessage("Checking backend connection...")
        self.run_button.setEnabled(False)

        try:
            # Health check (with timeout)
            if not self.backend_client.health_check_sync():
                self.toast_manager.show_error(
                    "Backend server is not running. Please check the terminal panel on the right for backend status.",
                    "Backend Connection Error",
                )
                self.statusBar().showMessage(
                    "❌ Backend not available - check terminal panel"
                )
                self.run_button.setEnabled(True)
                return

            # Serialize the graph
            self.statusBar().showMessage("Serializing graph...")
            graph_data = GraphSerializer.serialize_graph(self.nodes)

            pretty_print_payload(graph_data, "Graph Payload")

            # Load environment variables from settings
            env_vars = SettingsDialog.load_env_vars()

            # Log environment variables for debugging
            if env_vars:
                print(
                    f"[Editor] Loaded {len(env_vars)} environment variables from settings"
                )
                for key in env_vars.keys():
                    print(f"[Editor]   - {key}: {'*' * 8}")  # Mask values for security
            else:
                print("[Editor] No environment variables loaded from settings")

            # Create worker and thread
            self.execution_thread = QThread()
            self.execution_worker = ExecutionWorker(
                self.backend_client, graph_data, env_vars
            )
            self.execution_worker.moveToThread(self.execution_thread)

            # Connect signals
            self.execution_thread.started.connect(self.execution_worker.run)
            self.execution_worker.progress.connect(self._on_execution_progress)
            self.execution_worker.finished.connect(self._on_execution_finished)
            self.execution_worker.error.connect(self._on_execution_error)
            self.execution_worker.finished.connect(self.execution_thread.quit)
            self.execution_worker.error.connect(self.execution_thread.quit)
            self.execution_thread.finished.connect(self._on_thread_finished)

            # Clear any previous executing state
            if self._current_executing_node is not None:
                self._current_executing_node.graphics.set_executing_state(False)
                self._current_executing_node = None

            # Start execution
            self.statusBar().showMessage("Starting execution...")
            self.execution_thread.start()

        except Exception as e:
            self.toast_manager.show_error(
                f"Failed to start execution: {str(e)}",
                "Execution Error",
            )
            self.statusBar().showMessage(f"❌ Failed to start execution: {str(e)}")
            self.run_button.setEnabled(True)

    def _on_execution_progress(self, node_id: str, node_type: str):
        """Handle execution progress updates.

        Args:
            node_id: ID of the node being executed
            node_type: Type of the node being executed
        """
        # Extract node number from node_id (e.g., "node_0" -> "0")
        node_number = node_id.split("_")[-1] if "_" in node_id else node_id

        # Update status bar with current node being executed
        self.statusBar().showMessage(f"Executing Node {node_number}...")

    def _on_execution_finished(self, response: dict):
        """Handle execution completion.

        Args:
            response: Response dictionary with results
        """
        # Clear executing state from any executing node
        if self._current_executing_node is not None:
            self._current_executing_node.graphics.set_executing_state(False)
            self._current_executing_node = None

        # Update ViewNodes with results
        results = response.get("results", {})
        self._update_view_nodes_with_results(results)

        self.statusBar().showMessage("✓ Execution completed successfully")

    def _on_execution_error(self, error_message: str):
        """Handle execution errors.

        Args:
            error_message: Error message from execution
        """
        # Clear executing state from any executing node
        if self._current_executing_node is not None:
            self._current_executing_node.graphics.set_executing_state(False)
            self._current_executing_node = None

        self.toast_manager.show_error(
            f"Failed to execute graph: {error_message}",
            "Execution Error",
        )
        self.statusBar().showMessage(f"❌ Execution failed: {error_message}")

    def _on_thread_finished(self):
        """Handle thread cleanup after execution completes."""
        # Re-enable the run button
        self.run_button.setEnabled(True)

        # Clean up thread and worker
        if self.execution_thread:
            self.execution_thread.deleteLater()
            self.execution_thread = None
        if self.execution_worker:
            self.execution_worker.deleteLater()
            self.execution_worker = None

    def _update_view_nodes_with_results(self, results: dict):
        """Update ViewNodes with results from backend execution.

        Args:
            results: Dictionary mapping node IDs to their values
        """
        # Build a mapping from node IDs to ViewNode instances
        node_id_map = {}
        for i, node in enumerate(self.nodes):
            node_id = f"node_{i}"
            node_id_map[node_id] = node

        # Update each ViewNode
        for node_id, result_data in results.items():
            node = node_id_map.get(node_id)
            if node and isinstance(node, ViewNode):
                value = result_data.get("value")
                error = result_data.get("error")

                if error:
                    # Show error in ViewNode
                    node.display_text.setPlainText(f"Error: {error}")
                    node.graphics.set_error_state(True)
                else:
                    # Update display with value using ViewNode's set_value method
                    # This properly handles dictionaries and other complex types
                    node.set_value(value)
                    node.graphics.set_error_state(False)

    def _handle_node_error(self, node, exception: Exception):
        """Handle node execution errors by showing a toast notification."""
        node_id = id(node)
        error_message = f"{type(exception).__name__}: {str(exception)}"

        # Only show toast if this is a new error or different error message
        if (
            node_id not in self.current_errors
            or self.current_errors[node_id] != error_message
        ):
            self.current_errors[node_id] = error_message

            # Highlight the node with a red border
            node.graphics.set_error_state(True)

            self.toast_manager.show_error(
                error_message,
                node.title,
                on_close=lambda n=node: self._on_toast_closed(n),
            )
            # Pause execution when error occurs
            if not self.execution_paused:
                self.execution_paused = True
                self.statusBar().showMessage(
                    "⏸ Execution Paused - Fix error and close toast to resume"
                )

    def _on_toast_closed(self, node):
        """Handle toast close - resume execution to check if error is resolved."""
        node_id = id(node)

        # Clear the error from tracking
        if node_id in self.current_errors:
            del self.current_errors[node_id]

        # Clear the error highlight from the node
        node.graphics.set_error_state(False)

        # Resume execution - if error still exists, it will be caught again
        self.execution_paused = False
        self.statusBar().showMessage("▶ Execution Resumed")

    def resizeEvent(self, event):
        """Handle resize events to reposition toasts."""
        super().resizeEvent(event)
        if hasattr(self, "toast_manager"):
            self.toast_manager._reposition_toasts()

    def _load_graph_from_data(self, graph_data):
        """Load a graph from deserialized JSON data.

        Args:
            graph_data: Dictionary with 'nodes' and 'edges' keys
        """
        nodes_data = graph_data.get("nodes", [])
        edges_data = graph_data.get("edges", [])

        # Map to store node ID -> node instance
        node_id_map = {}
        # Map to store socket ID -> socket instance
        socket_id_map = {}

        # Create nodes
        for node_data in nodes_data:
            node_id = node_data["id"]
            node_type = node_data["type"]

            try:
                # Create node based on type
                if node_type == "object":
                    node = ObjectNode()
                elif node_type == "view":
                    node = ViewNode()
                elif node_type == "text":
                    node = TextNode()
                    # Restore TextNode params and value if they exist
                    params = node_data.get("params", {})
                    # Restore text value from output socket first (before return_as change)
                    output_sockets = node_data.get("output_sockets", [])
                    if output_sockets and "value" in output_sockets[0]:
                        text_value = output_sockets[0]["value"]
                        if text_value:
                            # Set the text in the editor
                            node.text_editor.setPlainText(text_value)
                            # Update current_value and output socket value
                            node.current_value = text_value
                            if node.output_sockets:
                                node.output_sockets[0].value = text_value
                    # Restore return_as after text is set (since changing return_as clears output socket)
                    if params:
                        return_as = params.get("return_as", "String")
                        if hasattr(node, "output_mode_selector"):
                            # Find the index of return_as in the combo box
                            for i in range(node.output_mode_selector.count()):
                                if node.output_mode_selector.itemData(i) == return_as:
                                    node.output_mode_selector.setCurrentIndex(i)
                                    break
                        # After setting return_as, restore the output socket value again
                        # (since _on_output_mode_changed clears it)
                        if output_sockets and "value" in output_sockets[0]:
                            text_value = output_sockets[0]["value"]
                            if text_value and node.output_sockets:
                                node.output_sockets[0].value = text_value
                elif node_type == "list":
                    node = ListNode()
                    # Restore the correct number of input sockets from saved data
                    input_sockets_data = node_data.get("input_sockets", [])
                    # Start with 1 socket, so we need to add (len - 1) more
                    while len(node.input_sockets) < len(input_sockets_data):
                        node._add_socket()
                elif node_type == "image":
                    node = ImageNode()
                    # Restore ImageNode params if they exist
                    params = node_data.get("params", {})
                    if params:
                        # Restore URL and path first (before mode change)
                        node.image_url = params.get("url", "")
                        node.image_path = params.get("path", "")
                        # Restore mode (this will trigger UI update)
                        mode = params.get("mode", "URL")
                        if hasattr(node, "mode_selector"):
                            # Find the index of the mode in the combo box
                            for i in range(node.mode_selector.count()):
                                if node.mode_selector.itemData(i) == mode:
                                    node.mode_selector.setCurrentIndex(i)
                                    break
                        # Restore return_as
                        return_as = params.get("return_as", "PIL Image")
                        if hasattr(node, "return_as_selector"):
                            # Find the index of return_as in the combo box
                            for i in range(node.return_as_selector.count()):
                                if node.return_as_selector.itemData(i) == return_as:
                                    node.return_as_selector.setCurrentIndex(i)
                                    break
                elif node_type == "dictionary":
                    node = DictionaryNode()
                    # Restore DictionaryNode entries from output socket value if available
                    output_sockets = node_data.get("output_sockets", [])
                    if output_sockets and "value" in output_sockets[0]:
                        dict_value = output_sockets[0]["value"]
                        if isinstance(dict_value, dict):
                            # Restore entries from dictionary value
                            node.entries = []
                            for key, value in dict_value.items():
                                # Infer type from value
                                if isinstance(value, bool):
                                    data_type = SocketDataType.BOOL
                                elif isinstance(value, int):
                                    data_type = SocketDataType.INT
                                elif isinstance(value, float):
                                    data_type = SocketDataType.FLOAT
                                elif isinstance(value, list):
                                    data_type = SocketDataType.LIST
                                elif isinstance(value, dict):
                                    data_type = SocketDataType.DICT
                                else:
                                    data_type = SocketDataType.STRING
                                node.entries.append(
                                    {"key": key, "type": data_type, "value": value}
                                )
                            if not node.entries:
                                # Ensure at least one empty entry
                                node.entries = [
                                    {
                                        "key": "",
                                        "type": SocketDataType.STRING,
                                        "value": "",
                                    }
                                ]
                            node._populate_table()
                            node._update_output()
                elif node_type == "pydantic_schema":
                    node = PydanticSchemaNode()
                    # Restore PydanticSchemaNode entries from params
                    params = node_data.get("params", {})
                    entries_data = params.get("entries", [])
                    if entries_data:
                        node.entries = []
                        for entry_data in entries_data:
                            field = entry_data.get("field", "")
                            type_str = entry_data.get("type", "str")
                            default_value = entry_data.get("default_value")

                            # Keep type as string (PydanticSchemaNode expects string types like "str", "list[str]", etc.)
                            node.entries.append(
                                {
                                    "field": field,
                                    "type": type_str,
                                    "default_value": default_value,
                                }
                            )
                        if not node.entries:
                            # Ensure at least one empty entry
                            node.entries = [
                                {
                                    "field": "",
                                    "type": "str",
                                    "default_value": None,
                                }
                            ]
                    # Restore schema_name from params
                    schema_name = params.get("schema_name")
                    if schema_name:
                        node.schema_name = schema_name
                        node.schema_name_input.setText(schema_name)
                    node._populate_table()
                    node._update_node_size()
                    node._update_output()
                else:
                    # OpNode - need to get schema
                    schema = self._get_node_schema(node_type)
                    if not schema:
                        self.toast_manager.show_error(
                            f"Unknown node type: {node_type}. Make sure the backend is running.",
                            "Load Warning",
                        )
                        continue
                    node = OpNode(schema)

                # Restore position and size from JSON if available
                position = node_data.get("position")
                size = node_data.get("size")

                if position and size:
                    # Position is stored as center coordinates, convert to top-left
                    center_x, center_y = position[0], position[1]
                    width, height = size[0], size[1]
                    top_left_x = center_x - width / 2
                    top_left_y = center_y - height / 2

                    # Set node size
                    node.graphics.width = width
                    node.graphics.height = height
                    node.graphics.setRect(0, 0, width, height)
                    # Reposition sockets after size change
                    node._position_sockets()

                    # Update widget sizes for nodes that have custom resize handlers
                    if hasattr(node, "_update_widget_sizes"):
                        node._update_widget_sizes()
                    elif hasattr(node, "_update_content_sizes"):
                        node._update_content_sizes()

                    # Set node position
                    node.set_position(top_left_x, top_left_y)
                else:
                    # Default position (will be arranged later if no positions saved)
                    node.set_position(0, 0)

                self.scene.addItem(node.graphics)
                self.nodes.append(node)

                if isinstance(node, ViewNode):
                    self.view_nodes.append(node)

                # Store in map
                node_id_map[node_id] = node

                # Map socket IDs to socket instances
                for i, socket in enumerate(node.input_sockets):
                    socket_id = f"{node_id}_input_{i}"
                    socket_id_map[socket_id] = socket

                for i, socket in enumerate(node.output_sockets):
                    socket_id = f"{node_id}_output_{i}"
                    socket_id_map[socket_id] = socket

                # Set input socket values from the data
                for socket_data in node_data.get("input_sockets", []):
                    socket_id = socket_data["id"]
                    if socket_id in socket_id_map:
                        socket = socket_id_map[socket_id]
                        value = socket_data.get("value")
                        if value is not None:
                            socket.value = value

            except Exception as e:
                self.toast_manager.show_error(
                    f"Failed to create node {node_id} ({node_type}): {str(e)}",
                    "Load Error",
                )

        # Create edges
        for edge_data in edges_data:
            start_socket_id = edge_data["start_socket"]
            end_socket_id = edge_data["end_socket"]

            if start_socket_id in socket_id_map and end_socket_id in socket_id_map:
                start_socket = socket_id_map[start_socket_id]
                end_socket = socket_id_map[end_socket_id]

                # Create edge
                edge = Edge(start_socket, end_socket)
                self.scene.addItem(edge.graphics)
                edge.update_positions()

                # Hide input widget for connected input sockets
                end_socket.set_input_widget_visible(False)

        # Arrange nodes in a grid layout only if they don't have saved positions
        # Check if any nodes have saved positions
        has_saved_positions = any(
            node_data.get("position") and node_data.get("size")
            for node_data in nodes_data
        )

        if not has_saved_positions:
            # No saved positions, arrange in grid layout
            self._arrange_loaded_nodes()
        else:
            # Nodes have saved positions, update edges for all nodes
            for node in self.nodes:
                node.update_edges()

        # Remove welcome message if nodes were loaded
        if self.nodes and hasattr(self, "welcome_text") and self.welcome_text:
            self.scene.removeItem(self.welcome_text)
            self.welcome_text = None

    def _get_node_schema(self, node_type):
        """Get schema for a node type from the backend.

        Args:
            node_type: Type name of the node (e.g., 'add', 'multiply')

        Returns:
            Schema dictionary or None if not found
        """
        try:
            # Try to get from backend
            response = self.backend_client.get_node_schemas_sync()
            schemas = response.get("nodes", [])

            for schema in schemas:
                if schema["name"] == node_type:
                    return schema

        except Exception as e:
            print(f"Failed to fetch schema for {node_type}: {e}")

        return None

    def _arrange_loaded_nodes(self):
        """Arrange loaded nodes in a grid layout."""
        if not self.nodes:
            return

        # Simple grid layout
        cols = 3
        spacing_x = 250
        spacing_y = 200
        start_x = -300
        start_y = -200

        for i, node in enumerate(self.nodes):
            row = i // cols
            col = i % cols
            x = start_x + col * spacing_x
            y = start_y + row * spacing_y
            node.set_position(x, y)

        # Update all edges
        for node in self.nodes:
            for socket in node.input_sockets + node.output_sockets:
                for edge in socket.edges:
                    edge.update_positions()

    def _add_welcome_message(self):
        """Add a welcome message to guide users."""
        from PySide6.QtGui import QColor

        welcome_text = QGraphicsTextItem()
        welcome_text.setPlainText(
            "Welcome to Psynapse!\n\n"
            "Drag nodes from the library panel on the left\n"
            "into the editor to add them.\n\n"
            "Drag from output (●) to input (●) to connect nodes."
        )
        welcome_text.setDefaultTextColor(QColor("#888888"))

        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        welcome_text.setFont(font)

        # Center the text
        welcome_text.setPos(-200, -100)

        self.scene.addItem(welcome_text)
        self.welcome_text = welcome_text

    def _add_node_internal(self, node_class, position=None):
        """Internal method to add a new node to the scene."""
        node = node_class()

        # Position at specified location or center of view
        if position:
            node.set_position(position.x(), position.y())
        else:
            view_center = self.view.viewport().rect().center()
            scene_pos = self.view.mapToScene(view_center)
            node.set_position(scene_pos.x() - 90, scene_pos.y() - 50)

        # Add to scene
        self.scene.addItem(node.graphics)

        # Track node
        self.nodes.append(node)
        if isinstance(node, ViewNode):
            self.view_nodes.append(node)

        return node

    def add_node_at_position(self, node_class_name, position):
        """Add a node at a specific position (called from drag-and-drop)."""
        if node_class_name in self.node_class_map:
            node_class = self.node_class_map[node_class_name]

            # Remove welcome message when first node is added
            if hasattr(self, "welcome_text") and self.welcome_text:
                self.scene.removeItem(self.welcome_text)
                self.welcome_text = None

            return self._add_node_internal(node_class, position)

    def closeEvent(self, event):
        """Handle close event - stop backend process and timer."""
        # Stop the current node polling timer
        if hasattr(self, "current_node_timer"):
            self.current_node_timer.stop()

        if hasattr(self, "terminal_panel"):
            self.terminal_panel.stop_backend()
        super().closeEvent(event)

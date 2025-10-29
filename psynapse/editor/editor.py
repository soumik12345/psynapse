from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont, QKeySequence
from PySide6.QtWidgets import (
    QGraphicsTextItem,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from psynapse.core.scene import NodeScene
from psynapse.core.serializer import GraphSerializer
from psynapse.core.view import NodeView
from psynapse.editor.backend_client import BackendClient
from psynapse.editor.node_library_panel import NodeLibraryPanel
from psynapse.editor.toast_notification import ToastManager
from psynapse.nodes.ops import ViewNode
from psynapse.utils import pretty_print_payload


class PsynapseEditor(QMainWindow):
    """Main node editor window."""

    def __init__(self):
        super().__init__()

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

        # Create splitter to hold library and view
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.node_library)
        splitter.addWidget(view_container)

        # Set initial sizes (library: 250px, view: rest)
        splitter.setSizes([250, 950])
        splitter.setStretchFactor(0, 0)  # Don't stretch library
        splitter.setStretchFactor(1, 1)  # Stretch view

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
        self.backend_client = BackendClient()

        # NOTE: Removed auto-execution timer - graphs are now executed on-demand via Run button

        # Add welcome message
        self._add_welcome_message()

        # Load node schemas from backend
        self._load_node_schemas()

        # Node class mapping for drag-and-drop (get from library panel)
        self.node_class_map = self.node_library.get_node_class_map()

        # Add status bar to show execution state
        self.statusBar().showMessage("Ready")

    def _create_menu_bar(self):
        """Create menu bar with node options."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._clear_scene)
        file_menu.addAction(new_action)

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

    def _load_node_schemas(self):
        """Load node schemas from the backend and populate the node library."""
        try:
            # Try to fetch schemas from backend
            response = self.backend_client.get_node_schemas_sync()
            # Backend returns {"nodes": [...]} not {"schemas": [...]}
            schemas = response.get("nodes", [])
            if schemas:
                self.node_library.load_schemas(schemas)
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
        self.scene.clear()
        self.nodes.clear()
        self.view_nodes.clear()
        self.welcome_text = None
        self._add_welcome_message()

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

    def _run_graph(self):
        """Execute the graph via the backend."""
        # Check if backend is available
        self.statusBar().showMessage("Checking backend connection...")
        self.run_button.setEnabled(False)

        try:
            # Health check (with timeout)
            if not self.backend_client.health_check_sync():
                self.toast_manager.show_error(
                    "Backend server is not running. Please start it with: uvicorn psynapse.backend.server:app --reload",
                    "Backend Connection Error",
                )
                self.statusBar().showMessage("❌ Backend not available")
                self.run_button.setEnabled(True)
                return

            # Serialize the graph
            self.statusBar().showMessage("Serializing graph...")
            graph_data = GraphSerializer.serialize_graph(self.nodes)

            pretty_print_payload(graph_data, "Graph Payload")

            # Execute on backend
            self.statusBar().showMessage("Executing on backend...")
            response = self.backend_client.execute_graph_sync(graph_data)

            # Update ViewNodes with results
            results = response.get("results", {})
            self._update_view_nodes_with_results(results)

            self.statusBar().showMessage("✓ Execution completed successfully")

        except Exception as e:
            self.toast_manager.show_error(
                f"Failed to execute graph: {str(e)}",
                "Execution Error",
            )
            self.statusBar().showMessage(f"❌ Execution failed: {str(e)}")

        finally:
            self.run_button.setEnabled(True)

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
                    # Update display with value
                    if value is None:
                        display_str = "None"
                    elif isinstance(value, float):
                        display_str = f"{value:.4g}"
                    else:
                        display_str = str(value)
                    node.display_text.setPlainText(display_str)
                    node.cached_value = value
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

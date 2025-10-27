from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QFont, QKeySequence
from PySide6.QtWidgets import QGraphicsTextItem, QMainWindow, QSplitter

from psynapse.core.scene import NodeScene
from psynapse.core.view import NodeView
from psynapse.editor.node_library_panel import NodeLibraryPanel
from psynapse.editor.toast_notification import ToastManager
from psynapse.nodes.ops import ViewNode


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

        # Create splitter to hold library and view
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.node_library)
        splitter.addWidget(self.view)

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

        # Set up auto-execution timer
        self.eval_timer = QTimer()
        self.eval_timer.timeout.connect(self._execute_graph)
        self.eval_timer.start(100)  # Execute every 100ms

        # Add welcome message
        self._add_welcome_message()

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

    def _execute_graph(self):
        """Execute all view nodes in the graph."""
        # Skip execution if paused due to error
        if self.execution_paused:
            return

        for view_node in self.view_nodes:
            view_node.execute_safe()

            # If node executed successfully and was previously in error, clear the highlight
            node_id = id(view_node)
            if node_id not in self.current_errors and view_node.graphics.has_error:
                view_node.graphics.set_error_state(False)

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

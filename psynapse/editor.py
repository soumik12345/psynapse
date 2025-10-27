"""Main node editor window."""

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction, QFont, QKeySequence
from PySide6.QtWidgets import QGraphicsTextItem, QMainWindow, QMenu

from psynapse.core.nodes import AddNode, MultiplyNode, SubtractNode, ViewNode
from psynapse.core.scene import NodeScene
from psynapse.core.view import NodeView


class PsynapseEditor(QMainWindow):
    """Main node editor window."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Psynapse - Node Editor")
        self.setGeometry(100, 100, 1200, 800)

        # Create scene and view
        self.scene = NodeScene()
        self.view = NodeView(self.scene)
        self.setCentralWidget(self.view)

        # Track all nodes
        self.nodes = []
        self.view_nodes = []

        # Create menu bar
        self._create_menu_bar()

        # Set up auto-execution timer
        self.eval_timer = QTimer()
        self.eval_timer.timeout.connect(self._execute_graph)
        self.eval_timer.start(100)  # Execute every 100ms

        # Context menu position
        self.context_pos = None

        # Add welcome message
        self._add_welcome_message()

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

        # Nodes menu
        nodes_menu = menubar.addMenu("&Nodes")

        add_node_action = QAction("Add Node", self)
        add_node_action.triggered.connect(lambda: self._add_node(AddNode))
        nodes_menu.addAction(add_node_action)

        subtract_node_action = QAction("Subtract Node", self)
        subtract_node_action.triggered.connect(lambda: self._add_node(SubtractNode))
        nodes_menu.addAction(subtract_node_action)

        multiply_node_action = QAction("Multiply Node", self)
        multiply_node_action.triggered.connect(lambda: self._add_node(MultiplyNode))
        nodes_menu.addAction(multiply_node_action)

        nodes_menu.addSeparator()

        view_node_action = QAction("View Node", self)
        view_node_action.triggered.connect(lambda: self._add_node(ViewNode))
        nodes_menu.addAction(view_node_action)

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
        for view_node in self.view_nodes:
            view_node.execute()

    def _add_welcome_message(self):
        """Add a welcome message to guide users."""
        from PySide6.QtGui import QColor

        welcome_text = QGraphicsTextItem()
        welcome_text.setPlainText(
            "Welcome to Psynapse!\n\n"
            "Right-click anywhere to add nodes\n"
            "or use the 'Nodes' menu at the top of your screen.\n\n"
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

    def _add_node(self, node_class):
        """Add a new node to the scene."""
        # Remove welcome message when first node is added
        if hasattr(self, "welcome_text") and self.welcome_text:
            self.scene.removeItem(self.welcome_text)
            self.welcome_text = None

        return self._add_node_internal(node_class)

    def _add_node_internal(self, node_class):
        """Internal method to add a new node to the scene."""
        node = node_class()

        # Position at center of view or at context menu position
        if self.context_pos:
            scene_pos = self.view.mapToScene(self.context_pos)
            node.set_position(scene_pos.x(), scene_pos.y())
            self.context_pos = None
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

    def contextMenuEvent(self, event):
        """Show context menu for adding nodes."""
        self.context_pos = event.pos()

        context_menu = QMenu(self)

        add_action = context_menu.addAction("Add Node")
        add_action.triggered.connect(lambda: self._add_node(AddNode))

        subtract_action = context_menu.addAction("Subtract Node")
        subtract_action.triggered.connect(lambda: self._add_node(SubtractNode))

        multiply_action = context_menu.addAction("Multiply Node")
        multiply_action.triggered.connect(lambda: self._add_node(MultiplyNode))

        context_menu.addSeparator()

        view_action = context_menu.addAction("View Node")
        view_action.triggered.connect(lambda: self._add_node(ViewNode))

        context_menu.exec(event.globalPos())

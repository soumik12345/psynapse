from typing import Any

from PySide6.QtCore import QRegularExpression, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
)
from PySide6.QtWidgets import (
    QComboBox,
    QGraphicsProxyWidget,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from psynapse.core.socket_types import SocketDataType
from psynapse.nodes.object_node import ObjectNode


class PythonHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Python code."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # Keyword format
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "and",
            "as",
            "assert",
            "break",
            "class",
            "continue",
            "def",
            "del",
            "elif",
            "else",
            "except",
            "False",
            "finally",
            "for",
            "from",
            "global",
            "if",
            "import",
            "in",
            "is",
            "lambda",
            "None",
            "nonlocal",
            "not",
            "or",
            "pass",
            "raise",
            "return",
            "True",
            "try",
            "while",
            "with",
            "yield",
            "async",
            "await",
        ]
        for word in keywords:
            pattern = QRegularExpression(f"\\b{word}\\b")
            self.highlighting_rules.append((pattern, keyword_format))

        # Built-in functions
        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor("#4ec9b0"))
        builtins = [
            "abs",
            "all",
            "any",
            "bin",
            "bool",
            "bytes",
            "chr",
            "dict",
            "dir",
            "enumerate",
            "filter",
            "float",
            "format",
            "int",
            "len",
            "list",
            "map",
            "max",
            "min",
            "open",
            "print",
            "range",
            "round",
            "set",
            "sorted",
            "str",
            "sum",
            "tuple",
            "type",
            "zip",
        ]
        for word in builtins:
            pattern = QRegularExpression(f"\\b{word}\\b")
            self.highlighting_rules.append((pattern, builtin_format))

        # String format (single and double quotes)
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.highlighting_rules.append((QRegularExpression('".*"'), string_format))
        self.highlighting_rules.append((QRegularExpression("'.*'"), string_format))

        # Comment format
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression("#[^\n]*"), comment_format))

        # Function/class names
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        self.highlighting_rules.append(
            (QRegularExpression("\\bdef\\s+(\\w+)"), function_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression("\\bclass\\s+(\\w+)"), function_format)
        )

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.highlighting_rules.append(
            (QRegularExpression("\\b[0-9]+\\.?[0-9]*\\b"), number_format)
        )

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text."""
        for pattern, format_style in self.highlighting_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(
                    match.capturedStart(), match.capturedLength(), format_style
                )


class MarkdownHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Markdown."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # Headers
        header_format = QTextCharFormat()
        header_format.setForeground(QColor("#569cd6"))
        header_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append(
            (QRegularExpression("^#{1,6}\\s.*$"), header_format)
        )

        # Bold
        bold_format = QTextCharFormat()
        bold_format.setForeground(QColor("#dcdcaa"))
        bold_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append(
            (QRegularExpression("\\*\\*[^*]+\\*\\*"), bold_format)
        )
        self.highlighting_rules.append((QRegularExpression("__[^_]+__"), bold_format))

        # Italic
        italic_format = QTextCharFormat()
        italic_format.setForeground(QColor("#ce9178"))
        italic_format.setFontItalic(True)
        self.highlighting_rules.append(
            (QRegularExpression("\\*[^*]+\\*"), italic_format)
        )
        self.highlighting_rules.append((QRegularExpression("_[^_]+_"), italic_format))

        # Code blocks
        code_format = QTextCharFormat()
        code_format.setForeground(QColor("#4ec9b0"))
        code_format.setBackground(QColor("#1e1e1e"))
        self.highlighting_rules.append((QRegularExpression("`[^`]+`"), code_format))

        # Links
        link_format = QTextCharFormat()
        link_format.setForeground(QColor("#4ec9b0"))
        link_format.setFontUnderline(True)
        self.highlighting_rules.append(
            (QRegularExpression("\\[([^\\]]+)\\]\\(([^)]+)\\)"), link_format)
        )

        # Lists
        list_format = QTextCharFormat()
        list_format.setForeground(QColor("#c586c0"))
        self.highlighting_rules.append(
            (QRegularExpression("^\\s*[-*+]\\s"), list_format)
        )
        self.highlighting_rules.append(
            (QRegularExpression("^\\s*\\d+\\.\\s"), list_format)
        )

        # Blockquotes
        quote_format = QTextCharFormat()
        quote_format.setForeground(QColor("#6a9955"))
        quote_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression("^>.*$"), quote_format))

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text."""
        for pattern, format_style in self.highlighting_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(
                    match.capturedStart(), match.capturedLength(), format_style
                )


class TextNode(ObjectNode):
    """Node for creating and editing multi-line text with syntax highlighting."""

    def __init__(self):
        # Don't call super().__init__() - we'll do our own initialization
        # Initialize the base Node class instead
        from psynapse.core.node import Node

        Node.__init__(
            self,
            title="Text",
            inputs=[],
            outputs=[("Value", SocketDataType.STRING)],
        )

        # Set fixed string type (no type selector needed)
        self.current_type = SocketDataType.STRING
        self.current_value = ""

        # Create container widget
        self.widget_container = QWidget()
        self.widget_layout = QVBoxLayout()
        self.widget_layout.setContentsMargins(0, 0, 0, 0)
        self.widget_layout.setSpacing(8)
        self.widget_layout.setAlignment(Qt.AlignCenter)
        self.widget_container.setLayout(self.widget_layout)

        # Create text type selector (for syntax highlighting)
        self.text_type_selector = QComboBox()
        self.text_type_selector.addItem("Plain Text", "plain")
        self.text_type_selector.addItem("Markdown", "markdown")
        self.text_type_selector.addItem("Python Code", "python")
        self.text_type_selector.setFixedWidth(300)
        self.text_type_selector.currentIndexChanged.connect(self._on_text_type_changed)

        # Style the text type selector (same style as ObjectNode)
        self.text_type_selector.setStyleSheet("""
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

        self.widget_layout.addWidget(self.text_type_selector)

        # Create text editor
        self.text_editor = QPlainTextEdit()
        self.text_editor.setFixedWidth(300)
        self.text_editor.setFixedHeight(200)
        self.text_editor.setPlaceholderText("Enter text...")
        self.text_editor.textChanged.connect(self._update_value)

        # Set monospace font for the editor
        font = QFont("Courier New", 10)
        self.text_editor.setFont(font)

        # Style the text editor
        self.text_editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 3px;
                padding: 8px;
                font-size: 11px;
            }
            QPlainTextEdit:focus {
                border: 1px solid #FF7700;
            }
        """)

        self.widget_layout.addWidget(self.text_editor)

        # Add widget to graphics and center it
        self.widget_proxy = QGraphicsProxyWidget(self.graphics)
        self.widget_proxy.setWidget(self.widget_container)
        # Set high z-value to ensure dropdown appears above other elements
        self.widget_proxy.setZValue(200)

        # Syntax highlighter (initially None for plain text)
        self.highlighter = None
        self.current_text_type = "plain"

        # Update the graphics width to accommodate the wider text editor
        self.graphics.width = 340

        # Increase node height to accommodate the text editor
        self.graphics.height = 320
        self.graphics.setRect(0, 0, self.graphics.width, self.graphics.height)

        # Add these attributes for compatibility with ObjectNode interface
        self.type_selector = None
        self.input_widget = self.text_editor

        # Update widget sizes and positions
        self._update_widget_sizes()

        # Override the graphics mouseMoveEvent to handle widget resizing
        self._original_mouse_move = self.graphics.mouseMoveEvent
        self.graphics.mouseMoveEvent = self._on_graphics_mouse_move

    def _on_text_type_changed(self, index: int):
        """Handle text type selector change to update syntax highlighting."""
        text_type = self.text_type_selector.itemData(index)
        self.current_text_type = text_type

        # Remove old highlighter if exists
        if self.highlighter:
            self.highlighter.setDocument(None)
            self.highlighter = None

        # Apply new highlighter based on selected type
        if text_type == "python":
            self.highlighter = PythonHighlighter(self.text_editor.document())
        elif text_type == "markdown":
            self.highlighter = MarkdownHighlighter(self.text_editor.document())
        # For plain text, no highlighter is needed

        # Force re-highlight
        if self.highlighter:
            self.highlighter.rehighlight()

    def _update_value(self):
        """Update the current value from the text editor."""
        self.current_value = self.text_editor.toPlainText()

        # Update output socket value
        if self.output_sockets:
            self.output_sockets[0].value = self.current_value

    def execute(self) -> Any:
        """Return the current text value."""
        return self.current_value

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
        available_width = max(120, self.graphics.width - left_margin - right_margin)

        # Calculate available height for text editor (account for type selector and margins)
        available_height = max(100, self.graphics.height - 120)

        # Update container width
        self.widget_container.setFixedWidth(available_width)

        # Update individual widget widths and heights
        self.text_type_selector.setFixedWidth(available_width)
        self.text_editor.setFixedWidth(available_width)
        self.text_editor.setFixedHeight(available_height)

        # Center the widget container horizontally in the node
        widget_x = (self.graphics.width - available_width) / 2
        self.widget_proxy.setPos(widget_x, 40)

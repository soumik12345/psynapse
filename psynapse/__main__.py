"""Main entry point for Psynapse node editor."""

import sys

from PySide6.QtWidgets import QApplication

from psynapse.editor import PsynapseEditor


def main():
    """Run the node editor application."""
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Psynapse")
    app.setOrganizationName("Psynapse")
    app.setApplicationVersion("0.1.0")

    # Create and show editor
    editor = PsynapseEditor()
    editor.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

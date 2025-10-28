import subprocess
import sys

import rich
from PySide6.QtWidgets import QApplication

from psynapse.editor import PsynapseEditor


def run_psynapse_editor():
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


def run_psynapse_backend():
    """Start the FastAPI backend server."""
    rich.print("[green]INFO:[/green]\t  Starting Psynapse backend server...")
    rich.print(
        "[green]INFO:[/green]\t  Backend will be available at http://localhost:8000"
    )
    rich.print(
        "[green]INFO:[/green]\t  Endpoints documentation will be available at http://localhost:8000/docs"
    )

    try:
        subprocess.run(
            ["uvicorn", "psynapse.backend.server:app", "--reload", "--host", "0.0.0.0"],
            check=True,
        )
    except KeyboardInterrupt:
        rich.print("\nShutting down backend server...")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        rich.print(f"Error starting backend: {e}", file=sys.stderr)
        sys.exit(1)

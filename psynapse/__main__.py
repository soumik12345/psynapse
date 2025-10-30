import argparse
import subprocess
import sys

import rich
from PySide6.QtWidgets import QApplication

from psynapse.editor import PsynapseEditor


def run_psynapse_editor():
    """Run the node editor application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Psynapse Node Editor")
    parser.add_argument(
        "--backend-port",
        type=int,
        default=None,
        help="Port of existing backend to connect to (if not specified, spawns new backend)",
    )
    args, unknown = parser.parse_known_args()

    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Psynapse")
    app.setOrganizationName("Psynapse")
    app.setApplicationVersion("0.1.0")

    # Create and show editor with backend port
    editor = PsynapseEditor(backend_port=args.backend_port)
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
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        rich.print(f"Error starting backend: {e}", file=sys.stderr)
        sys.exit(1)

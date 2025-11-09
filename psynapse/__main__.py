import subprocess
import sys
from typing import Optional

import typer
from PySide6.QtWidgets import QApplication
from rich import print as rprint

from psynapse.editor import PsynapseEditor

app = typer.Typer(help="Psynapse Node Editor CLI")


@app.command(name="editor")
def run_psynapse_editor(
    backend_port: Optional[int] = typer.Option(
        None,
        "--backend-port",
        "-p",
        help="Port of existing backend to connect to (if not specified, spawns new backend)",
    ),
):
    """Run the node editor application."""
    qt_app = QApplication(sys.argv)

    # Set application metadata
    qt_app.setApplicationName("Psynapse")
    qt_app.setOrganizationName("Psynapse")
    qt_app.setApplicationVersion("0.1.0")

    # Set global tooltip styling
    qt_app.setStyleSheet(
        """
        QToolTip {
            background-color: #2d2d2d;
            color: #ffffff;
            border: 1px solid #5a5a5a;
            border-radius: 4px;
            padding: 8px;
            font-size: 12px;
        }
        """
    )

    # Create and show editor with backend port
    editor = PsynapseEditor(backend_port=backend_port)
    editor.show()

    sys.exit(qt_app.exec())


@app.command(name="backend")
def run_psynapse_backend(
    host: str = typer.Option(
        "0.0.0.0", "--host", "-h", help="Host to bind the backend server to"
    ),
    port: int = typer.Option(
        8000, "--port", "-p", help="Port to bind the backend server to"
    ),
    reload: bool = typer.Option(
        True, "--reload/--no-reload", help="Enable auto-reload on code changes"
    ),
):
    """Start the FastAPI backend server."""
    rprint("[green]INFO:[/green]\t  Starting Psynapse backend server...")
    rprint(f"[green]INFO:[/green]\t  Backend will be available at http://{host}:{port}")
    rprint(
        f"[green]INFO:[/green]\t  Endpoints documentation will be available at http://{host}:{port}/docs"
    )

    cmd = [
        "uvicorn",
        "psynapse.backend.server:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if reload:
        cmd.append("--reload")

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        rprint(f"[red]Error starting backend: {e}[/red]", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    app()


def psynapse_cli():
    """Entry point for psynapse command - runs the editor by default."""
    # If no command is specified, run the editor command by default
    import sys

    if len(sys.argv) == 1 or (len(sys.argv) > 1 and not sys.argv[1].startswith("-")):
        # No command specified or starts with option, run editor
        if len(sys.argv) == 1:
            run_psynapse_editor()
        else:
            # Parse arguments for editor
            sys.argv.insert(1, "editor")
            app()
    else:
        # Likely an option, run editor
        sys.argv.insert(1, "editor")
        app()


def psynapse_backend_cli():
    """Entry point for psynapse-backend command."""
    import sys

    # Insert the backend command
    sys.argv.insert(1, "backend")
    app()


if __name__ == "__main__":
    main()

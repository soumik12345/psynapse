import subprocess
import sys
from typing import Optional

import typer
from PySide6.QtWidgets import QApplication
from rich import print as rprint

from psynapse.editor import PsynapseEditor

app = typer.Typer(help="Psynapse")


@app.command(name="editor")
def run_psynapse_editor(
    backend_port: Optional[int] = typer.Option(
        None,
        "--backend-port",
        "-p",
        help="Port of existing backend to connect to (if not specified, spawns new backend)",
    ),
    timeout_keep_alive: int = typer.Option(
        3600,
        "--timeout-keep-alive",
        "-t",
        help="Timeout for keep-alive connections in spawned backend (seconds)",
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

    # Create and show editor with backend port and timeout
    editor = PsynapseEditor(
        backend_port=backend_port, timeout_keep_alive=timeout_keep_alive
    )
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
    timeout_keep_alive: int = typer.Option(
        3600, "--timeout-keep-alive", "-t", help="Timeout for keep-alive connections"
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
        "--timeout-keep-alive",
        str(timeout_keep_alive),
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

    # If no command or only options are specified, insert 'editor' command
    if len(sys.argv) == 1:
        # No arguments, run editor
        sys.argv.insert(1, "editor")
    elif sys.argv[1] not in ["editor", "backend"]:
        # Argument is not a subcommand (likely an option), insert editor command
        if sys.argv[1].startswith("-"):
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

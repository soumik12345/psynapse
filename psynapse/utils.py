import json

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax


def pretty_print_payload(payload: dict, title: str):
    console = Console()
    console.print(
        Panel(
            Syntax(json.dumps(payload, indent=4), "json"),
            title=title,
        )
    )

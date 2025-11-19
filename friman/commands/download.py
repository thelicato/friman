import typer
from friman.utils.logger import frimanlog


app = typer.Typer()

@app.command()
def download():
    """Download a specific release file (e.g. server, gadget)."""

    frimanlog.error("WIP")
import typer
from friman.utils.logger import frimanlog


app = typer.Typer()

@app.command()
def push_server():
    """Pushes a the Frida server into the selected device."""

    frimanlog.error("WIP")
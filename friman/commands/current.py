import pathlib
import typer
from friman.utils import definitions
from friman.utils.logger import frimanlog


app = typer.Typer()

@app.command()
def current():
    """Display the currently activated version of Frida."""
    symlink_path = pathlib.Path(definitions.FRIMAN_CURRENT_FOLDER).resolve()

    if symlink_path.exists():
        frimanlog.success(f"Version in use is {symlink_path.name}")
    else:
        frimanlog.error("No version is currently set")
import typer
from friman.utils import helpers
from friman.utils.logger import frimanlog

app = typer.Typer()

@app.command()
def current():
    """Display the currently activated version of Frida."""
    current_version = helpers.get_current_version_in_use()

    if current_version != None:
        frimanlog.success(f"Version in use is {current_version}")
    else:
        frimanlog.error("No version is currently set")
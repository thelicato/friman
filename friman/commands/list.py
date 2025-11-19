import typer
from friman.utils import helpers
from friman.utils.logger import frimanlog

app = typer.Typer()

@app.command()
def list():
    """List all the installed versions."""
    installed_versions = helpers.get_installed_versions()
    if len(installed_versions) == 0:
        frimanlog.error("No installed versions")
        raise typer.Exit()
        
    frimanlog.info("Installed versions:")
    for version in installed_versions:
        frimanlog.info(f"\t{version}")
import typer
from friman.utils import helpers, definitions
from friman.utils.logger import frimanlog

app = typer.Typer()

@app.command()
def list():
    """List all the installed versions."""
    installed_versions = helpers.get_installed_versions()
    if len(installed_versions) == 0:
        frimanlog.error("No installed versions")
        raise typer.Exit()
        
    current_version = helpers.get_current_version_in_use()

    frimanlog.info("Installed versions:")
    sorted_tags = sorted(installed_versions, key=lambda s: tuple(map(int, s.split("."))))
    for version in sorted_tags:
        if (current_version == version):
            frimanlog.success(f"  {version} [*]")
        else:
            frimanlog.info(f"  {version}")
import os
import shutil
from typing_extensions import Annotated
import typer
from friman.utils import definitions, helpers
from friman.utils.logger import frimanlog

app = typer.Typer()

@app.command()
def uninstall(version: Annotated[str, typer.Argument(help="The version of Frida to uninstall", metavar="version")]):
    """Uninstall a <version> of Frida."""

    installed_versions = helpers.get_installed_versions()
    clean_version = version.replace("v","")

    if clean_version not in installed_versions:
        frimanlog.error(f"Version '{clean_version}' is not currently installed.")
        raise typer.Exit(1)
    
    shutil.rmtree(os.path.join(definitions.FRIMAN_ENV_FOLDER, clean_version))

    frimanlog.success(f"Version '{clean_version}' correctly uninstalled.")
import os
import pathlib
from typing_extensions import Annotated
import typer
from friman.utils import definitions, helpers
from friman.utils.logger import frimanlog


app = typer.Typer()

@app.command()
def use(version: Annotated[str, typer.Argument(help="The version of Frida to uninstall", metavar="version")]):
    """Use <version>."""

    installed_versions = helpers.get_installed_versions()
    clean_version = version.replace("v","")

    if clean_version not in installed_versions:
        frimanlog.error(f"Version '{clean_version}' is not currently installed.")
        raise typer.Exit(1)

    source = os.path.join(definitions.FRIMAN_ENV_FOLDER, clean_version)

    source_path = pathlib.Path(source).resolve()
    symlink_path = pathlib.Path(definitions.FRIMAN_CURRENT_FOLDER)

    if not source_path.is_dir():
        frimanlog.error(f"source is not a directory: {source_path}")
        raise typer.Exit(1)

    # Handle existing symlink or file
    if symlink_path.exists() or symlink_path.is_symlink():
        if symlink_path.is_symlink() or symlink_path.is_file():
            symlink_path.unlink()
        else:
            frimanlog.error(f"Destination exists and is not a symlink or file: {symlink_path}")
            raise typer.Exit(1)

    os.symlink(source_path, symlink_path, target_is_directory=True)
    frimanlog.success(f"Version in use correctly set to '{clean_version}'. Run 'frida --version' to check.")
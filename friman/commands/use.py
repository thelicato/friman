import os
import pathlib
import shutil
import shlex
from typing_extensions import Annotated
import typer
from friman.utils import definitions, helpers
from friman.utils.logger import frimanlog

app = typer.Typer()


def _warn_if_shadowed(env_path: str):
    """Switching the symlink cannot change the calling shell's PATH."""
    command = shutil.which("frida")
    expected = helpers.get_env_command_path(env_path, "frida")
    if command and pathlib.Path(command).resolve() == pathlib.Path(expected).resolve():
        return
    if command:
        frimanlog.warning(f"Your PATH still selects another Frida command: {command}")
    else:
        frimanlog.warning("The selected Frida command is not on your PATH.")
    entry = definitions.FRIMAN_BIN_FOLDER
    frimanlog.info("Put friman first in PATH in your current terminal:")
    if os.name == "nt":
        frimanlog.info(f'  CMD: set "PATH={entry};%PATH%"')
        escaped_entry = entry.replace("'", "''")
        frimanlog.info(f"  PowerShell: $env:PATH = '{escaped_entry};' + $env:PATH")
    else:
        frimanlog.info(f'  sh/bash/zsh: export PATH={shlex.quote(entry)}:"$PATH"')

@app.command()
def use(version: Annotated[str, typer.Argument(help="The version of Frida to use", metavar="version")]):
    """Use <version>."""

    installed_versions = helpers.get_installed_versions()
    clean_version = version.replace("v","")

    if clean_version not in installed_versions:
        frimanlog.error(f"Version '{clean_version}' is not currently installed.")
        raise typer.Exit(1)

    if not helpers.is_version_venv(clean_version):
        frimanlog.error(f"Version '{clean_version}' was installed with a legacy layout. Reinstall it with 'friman install {clean_version} --force' before using it.")
        raise typer.Exit(1)

    source = helpers.get_version_env_path(clean_version)

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
    helpers.create_current_bin_shims()
    frimanlog.success(f"Version in use correctly set to '{clean_version}'. Run 'frida --version' to check.")
    _warn_if_shadowed(source)

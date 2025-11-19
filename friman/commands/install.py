import os
import sys
import subprocess
from typing_extensions import Annotated
import typer
from friman.commands import update
from friman.utils import definitions, helpers
from friman.utils.logger import frimanlog

app = typer.Typer()

@app.command()
def install(
    version: Annotated[str, typer.Argument(help="The version of Frida to install", metavar="version")],
    force: bool = typer.Option(False, "--force", "-f", help="Force install."),
):
    """Install a <version> of Frida."""
    # TODO: Print something when the config is not updated in a while
    frida_tags = helpers.get_frida_tags()

    if len(frida_tags) == 0:
        frimanlog.error("The local list of available Frida versions is empty, running update...")
        update.update()

    clean_version = version.replace("v","")

    if clean_version.replace("v","") not in frida_tags:
        frimanlog.error(f"Version '{clean_version}' is not in the list of available Frida versions, currently available versions are: {frida_tags}. Run 'friman update' to get the list of all the available versions.")
        raise typer.Exit(1)

    frimanlog.info(f"Downloading version '{clean_version}'...")
    installed_versions = helpers.get_installed_versions()
    if clean_version in installed_versions and not force:
        frimanlog.info(f"Version '{clean_version}' is already installed. Use the '-f' option to force a reinstall.")
        raise typer.Exit()

    install_args = [
        sys.executable, 
        "-m", 
        "pip", 
        "install", 
        f"frida=={clean_version}", 
        "frida-tools", 
        "--upgrade",
        "--target", 
        os.path.join(definitions.FRIMAN_ENV_FOLDER, clean_version)
    ]
    install_result = subprocess.run(install_args, capture_output=True, text=True)

    if install_result.returncode != 0:
        frimanlog.error(f"Error while installing version '{clean_version}'. Run in the debug mode to get the full logs")
        frimanlog.debug(f"\n[STDOUT]\n {install_result.stdout}")
        frimanlog.debug(f"\n[STDERR]\n {install_result.stderr}")
        raise typer.Exit(1)

    frimanlog.success(f"Version '{clean_version}' correctly installed.")
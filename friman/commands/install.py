import sys
import shutil
import subprocess
from typing_extensions import Annotated
import typer
from friman.commands import update
from friman.utils import helpers
from friman.utils.logger import frimanlog

app = typer.Typer()

def list_callback(list):
    frida_tags = helpers.get_frida_tags()

    if (list):
        frimanlog.info("Available versions:")
        sorted_tags = sorted(frida_tags, key=lambda s: tuple(map(int, s.split("."))))
        for tag in sorted_tags:
            frimanlog.info(f"  {tag}")
        raise typer.Exit()

@app.command()
def install(
    version: Annotated[str, typer.Argument(help="The version of Frida to install", metavar="version")],
    force: bool = typer.Option(False, "--force", "-f", help="Force install."),
    list: bool = typer.Option(None,"--list", help="Show all the installable versions and exit.",callback=list_callback,is_eager=True)
):
    """Install a <version> of Frida."""
    
    # Get last update and Frida tags
    last_updated_at = helpers.get_config_updated_at()
    frida_tags = helpers.get_frida_tags()

    if len(frida_tags) == 0 or last_updated_at == None:
        frimanlog.error("The local list of available Frida versions is empty, running update...")
        update.update()
        frida_tags = helpers.get_frida_tags()
        last_updated_at = helpers.get_config_updated_at()
        
    if last_updated_at is not None and helpers.is_older_than(last_updated_at, 7):
        frimanlog.warning("You did not update the local list of available Frida versions for more than 7 days, please run 'friman update'.")

    clean_version = version.replace("v","")

    if clean_version.replace("v","") not in frida_tags:
        frimanlog.error(f"Version '{clean_version}' is not in the list of available Frida versions")
        frimanlog.error("Print the list of available versions with 'friman install --list'. If that version exists run 'friman update' to update the local list of all the available versions.")
        raise typer.Exit(1)

    frimanlog.info(f"Downloading version '{clean_version}'...")
    installed_versions = helpers.get_installed_versions()
    env_path = helpers.get_version_env_path(clean_version)
    if clean_version in installed_versions:
        if helpers.is_version_venv(clean_version):
            if not force:
                frimanlog.info(f"Version '{clean_version}' is already installed. Use the '-f' option to force a reinstall.")
                raise typer.Exit()
        else:
            if not force:
                frimanlog.error(f"Version '{clean_version}' was installed with a legacy layout. Reinstall it with '-f' to migrate it to a managed virtual environment.")
                raise typer.Exit(1)

        shutil.rmtree(env_path)

    venv_args = [
        sys.executable,
        "-m",
        "venv",
        env_path
    ]
    venv_result = subprocess.run(venv_args, capture_output=True, text=True)

    if venv_result.returncode != 0:
        shutil.rmtree(env_path, ignore_errors=True)
        frimanlog.error(f"Error while creating the environment for version '{clean_version}'. Run in the debug mode to get the full logs")
        frimanlog.debug(f"\n[STDOUT]\n {venv_result.stdout}")
        frimanlog.debug(f"\n[STDERR]\n {venv_result.stderr}")
        raise typer.Exit(1)

    install_args = [
        helpers.get_env_python_path(env_path),
        "-m", 
        "pip", 
        "install", 
        f"frida=={clean_version}", 
        "frida-tools", 
        "--upgrade"
    ]
    install_result = subprocess.run(install_args, capture_output=True, text=True)

    if install_result.returncode != 0:
        shutil.rmtree(env_path, ignore_errors=True)
        frimanlog.error(f"Error while installing version '{clean_version}'. Run in the debug mode to get the full logs")
        frimanlog.debug(f"\n[STDOUT]\n {install_result.stdout}")
        frimanlog.debug(f"\n[STDERR]\n {install_result.stderr}")
        raise typer.Exit(1)

    frimanlog.success(f"Version '{clean_version}' correctly installed.")

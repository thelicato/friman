import shutil
import tempfile
import subprocess
import re
from typing_extensions import Annotated
import typer
from friman.commands import download
from friman.utils import helpers
from friman.utils.logger import frimanlog

app = typer.Typer()

USB_DEVICE_TYPES = {"usb", "tether"}

def get_current_frida_command(command_name: str) -> str:
    current_env_path = helpers.get_current_env_path()
    if current_env_path is None:
        raise FileNotFoundError("No current environment selected")

    command_path = helpers.get_env_command_path(current_env_path, command_name)
    if not helpers.file_exists(command_path):
        raise FileNotFoundError(f"Missing command '{command_name}' in current environment")

    return command_path

def get_current_cli_version() -> str:
    frida_command = get_current_frida_command("frida")
    result = subprocess.run([frida_command, "--version"], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Failed to query Frida version")

    return result.stdout.strip()

def get_current_cli_devices():
    list_devices_command = get_current_frida_command("frida-ls-devices")
    result = subprocess.run([list_devices_command], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Failed to enumerate Frida devices")

    devices = []
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if len(stripped) == 0 or stripped.startswith("Id ") or stripped.startswith("---"):
            continue

        parts = re.split(r"\s{2,}", stripped)
        if len(parts) < 3:
            continue

        devices.append({
            "id": parts[0],
            "type": parts[1],
            "name": parts[2],
        })

    return devices

def list_devices():
    current_version = helpers.get_current_version_in_use()

    if current_version == None:
        frimanlog.error("No version is currently set.")
        raise typer.Exit(1)

    try:
        actual_version = get_current_cli_version()
        if actual_version != current_version:
            frimanlog.error(f"Mismatch between expected version and loaded one ('{current_version}' != '{actual_version}')")
            raise typer.Exit(1)

        return get_current_cli_devices()
    except typer.Exit:
        raise
    except FileNotFoundError:
        frimanlog.error(f"Version '{current_version}' is not a managed virtual environment. Reinstall it with 'friman install {current_version} --force'.")
        raise typer.Exit(1)
    except RuntimeError as ex:
        frimanlog.error("An error occurred while listing available devices. Reload with the '-d' option to get debug logs")
        frimanlog.debug(ex)
        raise typer.Exit(1)
    except Exception as ex:
        frimanlog.error("An error occurred while listing available devices. Reload with the '-d' option to get debug logs")
        frimanlog.debug(ex)
        raise typer.Exit(1)

def list_callback(list):
    devices = list_devices()
    usb_devices = [d for d in devices if d["type"] in USB_DEVICE_TYPES]

    if list:
        if len(usb_devices) > 0:
            frimanlog.info("Available devices:")
            for device in usb_devices:
                frimanlog.info(f"ID: {device['id']} - Name: {device['name']}")
        else:
            frimanlog.error("No devices available")
        raise typer.Exit()

@app.command()
def push_server(    
    device_id: Annotated[str, typer.Argument(help="The selected ANDROID device", metavar="device_id")],
    platform: Annotated[str, typer.Argument(help="The platform of the device", metavar="platform")],
    list: bool = typer.Option(None,"--list", help="Show all the USB devices and exit.",callback=list_callback,is_eager=True)
):
    """Pushes a the Frida server into the selected ANDROID device."""

    current_version = helpers.get_current_version_in_use()

    if current_version == None:
        frimanlog.error("No version is currently set.")
        raise typer.Exit(1)

    AVAILABLE_PLATFORMS = ["arm", "arm64", "x86", "x86_64"]

    if platform not in AVAILABLE_PLATFORMS:
        frimanlog.error(f"Invalid platform value '{platform}'. Available platforms are:")
        for p in AVAILABLE_PLATFORMS:
            frimanlog.error(f"  {p}")
        raise typer.Exit(1)

    devices = list_devices()
    usb_devices = [d for d in devices if d["type"] in USB_DEVICE_TYPES]
    device_ids = [d["id"] for d in usb_devices]

    if device_id not in device_ids:
        frimanlog.error(f"Invalid device ID '{platform}'. Available devices are:")
        for device in usb_devices:
            frimanlog.info(f"ID: {device['id']} - Name: {device['name']}")
        raise typer.Exit(1)

    # TODO: check for abd, download frida-server for the specified platform and run adb push

    # Check if 'adb' available in PATH, here we are assuming the user specified an Android device
    adb_path = shutil.which("adb")
    if adb_path == None:
        frimanlog.error("adb is not available in the PATH")
        raise typer.Exit(1)
    
    # Download Frida server (matching current version) for the specified platform
    frida_server_xz_path = download.download("server", f"android-{platform}", tempfile.gettempdir())
    frida_server_path = helpers.extract_xz(frida_server_xz_path, True)
    frida_server_name = frida_server_path.split("/")[-1]

    # Push it to /data/local/tmp
    adb_push_args = [adb_path, "-s", device_id, "push", frida_server_path, f"/data/local/tmp/{frida_server_name}"]
    push_result = subprocess.run(adb_push_args, capture_output=True, text=True)

    if push_result.returncode != 0:
        frimanlog.error(f"Error while pushing '{frida_server_name}'. Run in the debug mode to get the full logs")
        frimanlog.debug(f"\n[STDOUT]\n {push_result.stdout}")
        frimanlog.debug(f"\n[STDERR]\n {push_result.stderr}")
        raise typer.Exit(1)
    
    frimanlog.success(f"Frida server was correctly pushed at '/data/local/tmp/{frida_server_name}'.")

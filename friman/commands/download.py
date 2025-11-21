import os
from pathlib import Path
from urllib.parse import urlparse
from typing_extensions import Annotated
import typer
from friman.utils import helpers, definitions
from friman.utils.logger import frimanlog

app = typer.Typer()

AVAILABLE_ASSETS_MAPPING = {
    "gadget": ["android-arm", "android-arm64", "android-x86", "android-x86_64", "ios-universal", "ios-simulator-universal", "freebsd-x86_64", "linux-arm64-musl", "linux-arm64", "linux-armhf", "linux-arm64be", "linux-armbe8", "linux-armhf-musl", "linux-x86", "linux-x86_64", "linux-x86_64-musl", "linux-mips", "linux-mips64", "linux-mips64el", "linux-mipsel", "macos-universal", "qnx-armeabi", "tvos-arm64-simulator", "tvos-arm64", "watchos-arm64-simulator", "watchos-arm64", "windows-arm64", "windows-x86", "windows-x86_64"],
    "server": ["android-arm", "android-arm64", "android-x86", "android-x86_64", "freebsd-x86_64", "linux-arm64-musl", "linux-arm64", "linux-arm64be", "linux-armbe8", "linux-armhf-musl", "linux-armhf", "linux-mips", "linux-mips64", "linux-mips64el", "linux-mipsel", "linux-x86", "linux-x86_64-musl", "linux-x86_64", "macos-arm64", "macos-arm64e", "macos-x86_64", "windows-arm64", "windows-x86", "windows-x86_64", "qnx-armeabi"]
}

@app.command()
def download(
    asset_type: Annotated[str, typer.Argument(help="The selected asset type", metavar="type")],
    platform: Annotated[str, typer.Argument(help="The platform to use", metavar="platform")],
    out_dir: str = typer.Option(None,"--output", "-o", help="Select the folder where to download the file.")
):
    """Download a specific release file (only server and gadget) for the current version."""

    current_version = helpers.get_current_version_in_use()

    if current_version == None:
        frimanlog.error("No version is currently set.")
        raise typer.Exit(1)
    
    output_dir = os.path.abspath(out_dir if out_dir != None else Path.cwd())
    if not os.access(output_dir, os.W_OK):
        frimanlog.error(f"No permissions to save files in '{output_dir}'.")
        raise typer.Exit(1)
    
    if not os.path.isdir(output_dir):
        frimanlog.error(f"Invalid output dir '{output_dir}'.")
        raise typer.Exit(1)

    if asset_type not in list(AVAILABLE_ASSETS_MAPPING.keys()):
        frimanlog.error(f"Invalid type value '{asset_type}'. Available asset types are:")
        for available_asset_type in AVAILABLE_ASSETS_MAPPING.keys():
            frimanlog.error(f"  {available_asset_type}")
        raise typer.Exit(1)
    
    if platform not in AVAILABLE_ASSETS_MAPPING[asset_type]:
        frimanlog.error(f"Invalid platform value '{platform}'. Available platforms for '{asset_type}' are:")
        for available_platforms in AVAILABLE_ASSETS_MAPPING[asset_type]:
            frimanlog.error(f"  {available_platforms}")
        raise typer.Exit(1)

    available_assets = helpers.get_github_release_assets(definitions.FRIDA_REPO, current_version)

    asset_names = [a[0] for a in available_assets]
    
    prefix = f"frida-{asset_type}-{current_version}-{platform}."
    candidates = [a for a in available_assets if a[0].startswith(prefix)]

    if len(candidates) == 0:
        frimanlog.error(f"Unable to find 'frida-{asset_type}' for version {current_version} and platform {platform}. Available assets for this version are:")
        for asset in asset_names:
            if asset.startswith(f"frida-{asset_type}"):
                frimanlog.info(f"  {asset}")

    chosen_one = candidates[0]
    frimanlog.info(f"Downloading '{chosen_one[0]}' at {chosen_one[1]}...")

    parsed = urlparse(chosen_one[1])
    host = parsed.netloc
    url  = parsed.path
    data = helpers.make_request(host, url, helpers.get_base_headers(), True)

    output_file = chosen_one[0] if output_dir == None else os.path.join(output_dir, chosen_one[0])
    with open(output_file, "wb") as f:
        f.write(data)
    
    frimanlog.success(f"File correctly saved at '{output_file}'")
    return output_file
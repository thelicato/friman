import os
import platform
from pathlib import Path, PureWindowsPath
import typer
from friman.utils import definitions
from friman.utils.logger import frimanlog

app = typer.Typer()

@app.command()
def ensurepath():
    """Ensure friman directories are correctly set."""

    system = platform.system().lower()

    # ----- Check if already in PATH -----
    path_entry = str(PureWindowsPath(definitions.FRIMAN_CURRENT_FOLDER) / "Scripts") if system == "windows" else os.path.join(definitions.FRIMAN_CURRENT_FOLDER, "bin")
    current_path = os.environ.get("PATH", "")
    if path_entry in current_path:
        frimanlog.info(f"Already in PATH: {path_entry}")
    else:
        frimanlog.info(f"PATH does not contain {path_entry}")

    # ----- Determine where to write -----
    if system == "windows":
        # Modify the user's PowerShell profile on Windows
        profile = Path(os.environ["USERPROFILE"]) / "Documents" / "WindowsPowerShell" / "profile.ps1"
        line = (
            f'\n# Added by friman\n'
            f'$env:PATH += ";{path_entry}"\n'
            f'$env:PYTHONPATH = "{definitions.FRIMAN_CURRENT_FOLDER};$env:PYTHONPATH"\n'
        )
    else:
        # Modify the shell startup file (bash or zsh)
        # Try ~/.bashrc first
        shell = os.environ.get("SHELL", "")
        if "zsh" in shell:
            rcfile = Path.home() / ".zshrc"
        else:
            rcfile = Path.home() / ".bashrc"
        profile = rcfile
        line = f'\n# Added by friman\nexport PATH="{path_entry}:$PATH"\nexport PYTHONPATH="{definitions.FRIMAN_CURRENT_FOLDER}:$PYTHONPATH"\n'

    # ----- Append if missing -----
    if profile.exists():
        contents = profile.read_text()
        if path_entry in contents or definitions.FRIMAN_CURRENT_FOLDER in contents:
            frimanlog.info(f"Already added in {profile}")
            return

    profile.parent.mkdir(parents=True, exist_ok=True)
    with open(profile, "a", encoding="utf8") as f:
        f.write(line)

    frimanlog.success(f"Added PATH entry to {profile}")
    frimanlog.info("Restart your terminal for changes to take effect.")

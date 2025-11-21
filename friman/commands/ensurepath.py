import os
import platform
from pathlib import Path
import typer
from friman.utils import definitions
from friman.utils.logger import frimanlog

app = typer.Typer()

@app.command()
def ensurepath():
    """Ensure friman directories are correctly set."""

    system = platform.system().lower()
    bin_path = os.path.join(definitions.FRIMAN_CURRENT_FOLDER, "bin")

    # ----- Check if already in PATH -----
    current_path = os.environ.get("PATH", "")
    if definitions.FRIMAN_CURRENT_FOLDER in current_path:
        frimanlog.info(f"Already in PATH: {definitions.FRIMAN_CURRENT_FOLDER}")
    else:
        frimanlog.info(f"PATH does not contain {definitions.FRIMAN_CURRENT_FOLDER}")

    # ----- Determine where to write -----
    if system == "windows":
        # Modify the user's PowerShell profile on Windows
        profile = Path(os.environ["USERPROFILE"]) / "Documents" / "WindowsPowerShell" / "profile.ps1"
        line = f'$env:PATH += ";{definitions.FRIMAN_CURRENT_FOLDER}"\n'
    else:
        # Modify the shell startup file (bash or zsh)
        # Try ~/.bashrc first
        shell = os.environ.get("SHELL", "")
        if "zsh" in shell:
            rcfile = Path.home() / ".zshrc"
        else:
            rcfile = Path.home() / ".bashrc"
        profile = rcfile
        line = f'\n# Added by friman\nexport PATH="{bin_path}:$PATH"\nexport PYTHONPATH="{definitions.FRIMAN_CURRENT_FOLDER}:$PYTHONPATH"\n'

    # ----- Append if missing -----
    if profile.exists():
        contents = profile.read_text()
        if definitions.FRIMAN_CURRENT_FOLDER in contents:
            frimanlog.info(f"Already added in {profile}")
            return

    profile.parent.mkdir(parents=True, exist_ok=True)
    with open(profile, "a", encoding="utf8") as f:
        f.write(line)

    frimanlog.success(f"Added PATH entry to {profile}")
    frimanlog.info("Restart your terminal for changes to take effect.")
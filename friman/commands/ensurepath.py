import os
import platform
import re
from pathlib import Path
import typer
from friman.utils import definitions, helpers
from friman.utils.logger import frimanlog

app = typer.Typer()

FRIMAN_BLOCK_START = "# >>> friman >>>"
FRIMAN_BLOCK_END = "# <<< friman <<<"

def get_path_entry(system: str) -> str:
    return definitions.FRIMAN_BIN_FOLDER

def build_profile_block(system: str, shell: str, path_entry: str) -> str:
    if system == "windows":
        return (
            f"{FRIMAN_BLOCK_START}\n"
            f'$env:PATH += ";{path_entry}"\n'
            f"{FRIMAN_BLOCK_END}\n"
        )

    shell_name = Path(shell).name if shell else ""
    if shell_name == "fish":
        return (
            f"{FRIMAN_BLOCK_START}\n"
            f'set -gx PATH "{path_entry}" $PATH\n'
            f"{FRIMAN_BLOCK_END}\n"
        )

    return (
        f"{FRIMAN_BLOCK_START}\n"
        f'export PATH="{path_entry}:$PATH"\n'
        f"{FRIMAN_BLOCK_END}\n"
    )


def get_shell_profile(system: str, shell: str) -> Path:
    if system == "windows":
        return Path(os.environ["USERPROFILE"]) / "Documents" / "WindowsPowerShell" / "profile.ps1"

    shell_name = Path(shell or "").name.lower()
    if shell_name == "fish":
        return Path.home() / ".config" / "fish" / "config.fish"
    if shell_name == "zsh":
        return Path.home() / ".zshrc"
    if shell_name == "bash":
        return Path.home() / ".bashrc"
    if shell_name == "ksh":
        return Path.home() / ".kshrc"
    if shell_name == "tcsh":
        return Path.home() / ".tcshrc"
    if shell_name == "csh":
        return Path.home() / ".cshrc"

    return Path.home() / ".profile"


def remove_managed_blocks(contents: str) -> str:
    contents = re.sub(
        rf"\n?{re.escape(FRIMAN_BLOCK_START)}\n.*?\n{re.escape(FRIMAN_BLOCK_END)}\n?",
        "\n",
        contents,
        flags=re.DOTALL,
    )
    contents = re.sub(
        r'\n?# Added by friman\nexport PATH="[^"\n]+:\$PATH"\nexport PYTHONPATH="[^"\n]+:\$PYTHONPATH"\n?',
        "\n",
        contents,
    )
    contents = re.sub(
        r'\n?# Added by friman\n\$env:PATH \+= ";[^"\n]+"\n(?:\$env:PYTHONPATH = "[^"\n]+"\n)?',
        "\n",
        contents,
    )
    return contents.strip("\n")

@app.command()
def ensurepath():
    """Ensure friman directories are correctly set."""

    system = platform.system().lower()
    shell = os.environ.get("SHELL", "")
    path_entry = get_path_entry(system)

    current_path = os.environ.get("PATH", "")
    if path_entry in current_path:
        frimanlog.info(f"Already in PATH: {path_entry}")
    else:
        frimanlog.info(f"PATH does not contain {path_entry}")

    profile = get_shell_profile(system, shell)

    profile.parent.mkdir(parents=True, exist_ok=True)
    block = build_profile_block(system, shell, path_entry)

    contents = profile.read_text(encoding="utf8") if profile.exists() else ""
    if FRIMAN_BLOCK_START in contents and FRIMAN_BLOCK_END in contents and path_entry in contents:
        frimanlog.info(f"Already added in {profile}")
        helpers.create_current_bin_shims()
        return

    cleaned_contents = remove_managed_blocks(contents)
    new_contents = f"{cleaned_contents}\n{block}" if cleaned_contents else block

    with open(profile, "w", encoding="utf8") as f:
        f.write(new_contents)

    helpers.create_current_bin_shims()
    frimanlog.success(f"Updated PATH entry in {profile}")
    frimanlog.info("Restart your terminal for changes to take effect.")

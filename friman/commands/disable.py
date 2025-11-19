import pathlib
import typer
from friman.utils import definitions
from friman.utils.logger import frimanlog


app = typer.Typer()

@app.command()
def disable():
    """Disable friman."""

    symlink_path = pathlib.Path(definitions.FRIMAN_CURRENT_FOLDER)
    
    if not symlink_path.exists() and not symlink_path.is_symlink():
        frimanlog.error("friman is not currently set")
        raise typer.Exit(1)

    # Handle existing symlink or file
    if symlink_path.is_symlink() or symlink_path.is_file():
        symlink_path.unlink()
    else:
        frimanlog.error(f"Destination exists and is not a symlink or file: {symlink_path}")
        raise typer.Exit(1)

    frimanlog.success(f"friman correctly deactivated")
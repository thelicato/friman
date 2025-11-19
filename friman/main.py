import typer
from friman import __title__, __version__, __description__
from friman.utils.helpers import banner

app = typer.Typer(add_completion=False, context_settings={"help_option_names": ["-h", "--help"]})

@app.command()
def install():
    """Install a <version> of Frida."""
    pass

@app.command()
def uninstall():
    """Uninstall a <version> of Frida."""
    pass

@app.command()
def use():
    """Modify PATH to use <version>."""
    pass

@app.command()
def list():
    """List all the installed versions."""
    pass

@app.command()
def current():
    """Display the currently activated version of Frida."""
    pass

@app.command()
def ensurepath():
    """Ensure friman directories are correctly set."""
    pass

@app.command()
def download():
    """Download a specific release file (e.g. server, gadget)."""
    pass

@app.command()
def push_server():
    """Pushes a the Frida server into the selected device."""
    pass


def version_callback(value: bool):
    if value:
        print(__version__)
        raise typer.Exit()
    else:
        banner(__version__)


@app.callback(invoke_without_command=True)
def cli(
    ctx: typer.Context,
    _version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=version_callback,
        is_eager=True,   # ensures -v is processed before other logic
    ),
):
    # If no subcommand was given then show help
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


def main():
    """The main entrypoint"""
    app()

if __name__ == "__main__":
    main()
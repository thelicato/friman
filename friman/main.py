import typer
from friman import __title__, __version__, __description__
from friman.commands import update, install, uninstall, use, disable, current, list, ensurepath, download, pushserver
from friman.utils import helpers, definitions

app = typer.Typer(add_completion=False, context_settings={"help_option_names": ["-h", "--help"]})
app.add_typer(update.app)
app.add_typer(install.app)
app.add_typer(uninstall.app)
app.add_typer(use.app)
app.add_typer(disable.app)
app.add_typer(current.app)
app.add_typer(list.app)
app.add_typer(ensurepath.app)
app.add_typer(download.app)
app.add_typer(pushserver.app)

def version_callback(value: bool):
    if value:
        print(__version__)
        raise typer.Exit()
    else:
        helpers.banner(__version__)
        helpers.ensure_folders()
        print()

def debug_callback(value: bool):
    helpers.set_env_if_empty(definitions.FRIMAN_DEBUG, str(int(value)))  # "1" if True, "0" otherwise

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
    _debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Show debug output.",
        callback=debug_callback,
        is_eager=True,   # ensures -d is processed before other logic
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
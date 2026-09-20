import json
from datetime import datetime
import typer
from friman.utils import helpers, definitions
from friman.utils.logger import frimanlog
from friman.utils.exceptions import RateLimitException

app = typer.Typer()

@app.command()
def update():
    """Update the local list of available Frida versions."""

    frimanlog.info("Setting up the list of available Frida versions...")
    try:
        current_config = helpers.get_current_config()
        frida_tags = helpers.get_pypi_versions(definitions.FRIDA_PYPI)
        current_config[definitions.FRIMAN_CONFIG_TAGS] = frida_tags
        current_config[definitions.FRIMAN_CONFIG_UPDATED_AT] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(definitions.FRIMAN_CONFIG_FILE, "w") as f:
            json.dump(current_config, f, ensure_ascii=False, indent=2)
        frimanlog.success(f"{definitions.FRIMAN_CONFIG_FILE} updated!")

        frimanlog.info("Updating the Frida compatibility matrix...")
        helpers.download_compatibility_matrix()
        frimanlog.success(f"{definitions.FRIMAN_COMPATIBILITY_MATRIX_FILE} updated!")
    except RateLimitException as ex:
        frimanlog.error(f"GitHub API rate limit reached while updating metadata: {ex}")
        frimanlog.info("Set GITHUB_TOKEN to authenticate GitHub requests, or retry after the rate limit resets.")
        raise typer.Exit(1)
    except Exception as ex:
        frimanlog.error(f"An error occurred while updating the list of Frida tags: {ex}")
        raise typer.Exit(1)

"""
This modules contains the all the static definitions
"""

from os import path
from pathlib import Path

FILE_PATH = Path(__file__)
ROOT_DIR = FILE_PATH.parent.parent.parent.absolute()  # The path of the root folder
MAIN_DIR = FILE_PATH.parent.parent.absolute()  # The path of the 'friman' folder within the project

# Common definitions
DEFAULT_BASE_PATH = ".friman"
FRIMAN_FOLDER = path.join(Path.home(), DEFAULT_BASE_PATH)

# Definitions for the folders
FRIMAN_ENV_FOLDER = path.join(FRIMAN_FOLDER, "env") # Folder that contains all the installed frida versions
FRIMAN_BIN_FOLDER = path.join(FRIMAN_FOLDER, "bin") # Folder that links to the currently used frida version
FRIMAN_SERVER_FOLDER = path.join(FRIMAN_FOLDER, "server") # Folder that contains the downloaded frida servers

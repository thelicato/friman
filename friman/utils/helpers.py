"""
This module contains multiple helper function used throughout the codebase.
"""
import os
from .definitions import FRIMAN_FOLDER, FRIMAN_BIN_FOLDER, FRIMAN_ENV_FOLDER, FRIMAN_SERVER_FOLDER

def banner(version):
    print()
    print(f" friman v{version}")

def create_folder_if_missing(path: str) -> None:
    """Utility function to create a folder if missing"""
    if not os.path.isdir(path):
        os.makedirs(path)

def ensure_folders():
    # Create the .friman folder in $HOME if missing
    create_folder_if_missing(FRIMAN_FOLDER)

    # Create the bin, env and server folders within the above one if missing
    create_folder_if_missing(FRIMAN_BIN_FOLDER)
    create_folder_if_missing(FRIMAN_ENV_FOLDER)
    create_folder_if_missing(FRIMAN_SERVER_FOLDER)
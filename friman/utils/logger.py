import os
import sys
from friman.utils import definitions

class Logger:
    COLORS = {
        "DEBUG": "\033[94m",            # Blue
        "INFO": "",                     # None
        "SUCCESS": "\033[92m",          # Green
        "WARNING": "\033[38;5;214m",    # Orange (256-color escape)
        "ERROR": "\033[91m",            # Red
        "RESET": "\033[0m",
        "BOLD": "\033[1m"
    }

    LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"]
    # compute padding to align levels
    _max_len = max(len(level) for level in LEVELS)

    def _log(self, level: str, message: str, bold: bool = False):
        color = self.COLORS[level]
        reset = self.COLORS["RESET"]
        bold = self.COLORS["BOLD"] if bold else ''
        # Align type with spaces inside brackets
        #padded_level = f"{level:<{self._max_len}}"
        #log_line = f"[{color}{padded_level}{reset}] {bold}{message}{reset}"
        log_line = f"{color}{bold}{message}{reset}"
        print(log_line, file=sys.stdout)

    def debug(self, message: str, bold: bool = False):
        debug_env_value = os.environ.get(definitions.FRIMAN_DEBUG, str(int(False)))
        is_debug = True if debug_env_value == "1" else False
        if is_debug:
            self._log("DEBUG", message, bold)

    def info(self, message: str, bold: bool = False):
        self._log("INFO", message, bold)

    def success(self, message: str, bold: bool = False):
        self._log("SUCCESS", message, bold)

    def warning(self, message: str, bold: bool = True):
        self._log("WARNING", message, bold)

    def error(self, message: str, bold: bool = True):
        self._log("ERROR", message, bold)


# Create a single shared instance
frimanlog = Logger()
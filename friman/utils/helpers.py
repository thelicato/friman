"""
This module contains multiple helper function used throughout the codebase.
"""
import os
import pathlib
import json
import lzma
import http.client
from urllib.parse import urlparse, urljoin
from datetime import datetime, timedelta
from packaging.version import Version, InvalidVersion
from friman.utils import definitions, exceptions
from friman.utils.logger import frimanlog

def banner(version):
    print()
    print(f"friman v{version}")

def file_exists(filepath: str) -> bool:
    """Check if a file exists at the given filepath and return a boolean."""
    return os.path.exists(filepath)

def create_folder_if_missing(path: str) -> None:
    """Utility function to create a folder if missing"""
    if not os.path.isdir(path):
        os.makedirs(path)

def ensure_folders():
    # Create the .friman folder in $HOME if missing
    create_folder_if_missing(definitions.FRIMAN_FOLDER)

    # Create the env folder within the above one if missing
    create_folder_if_missing(definitions.FRIMAN_ENV_FOLDER)

def set_env_if_empty(env_var, env_value):
    """Set an ENV variable if empty, otherwise don't change it (ENV vars take precedence!)"""
    os.environ[env_var] = os.environ.get(env_var, env_value)

def get_base_headers():
    """Get basic request headers"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.3"
    }
    return headers


def get_github_headers():
    """Returns GitHub authentication headers if a token is available."""
    github_token = os.getenv('GITHUB_TOKEN')
    headers = get_base_headers()

    if github_token:
        headers["Authorization"] = f"token {github_token}"
    return headers


def make_request(host, url, headers, follow_redirects=False, max_redirects=5):
    """Performs an HTTPS GET request and returns the response."""

    redirects = 0
    current_host = host
    current_url = url

    while True:
        conn = http.client.HTTPSConnection(current_host)
        conn.request("GET", current_url, headers=headers)
        response = conn.getresponse()

        status = response.status
        data = response.read()
        conn.close()

        # Handle redirect
        if follow_redirects and status in (301, 302, 303, 307, 308):
            if redirects >= max_redirects:
                raise Exception("Too many redirects")

            location = response.getheader("Location")
            if not location:
                raise Exception("Redirect without Location header")

            # Build new absolute URL
            if location.startswith("http"):
                parsed = urlparse(location)
                current_host = parsed.netloc
                current_url = parsed.path or "/"
                if parsed.query:
                    current_url += "?" + parsed.query
            else:
                # relative redirect
                current_url = urljoin(current_url, location)

            redirects += 1
            continue  # perform another request

        # Normal error handling
        if status == 403:
            raise exceptions.RateLimitException(f"Status code {response.status} - error {data.decode()} - url {url}")
        elif status != 200:
            raise Exception(f"{status} - {data.decode()} - url {current_url}")

        return data

def get_all_github_tags(repo: str):
    """Fetches all tags from the GitHub repository, handling pagination."""
    tags = []
    page = 1

    while True:
        url = f"{definitions.GITHUB_API['repos']}/{repo}{definitions.GITHUB_API['tags']}?page={page}"
        headers = get_github_headers()
        
        data = make_request(definitions.GITHUB_API['base'], url, headers)
        results = json.loads(data)

        if not results:
            break

        tags.extend([tag["name"] for tag in results])
        page += 1

    return tags

def get_pypi_versions(package: str):
    """Fetches all the available versions of a package from PyPI"""
    tags = []
    url = f"{definitions.PYPI_API['pypi']}/{package}{definitions.PYPI_API['json']}"

    data = make_request(definitions.PYPI_API['base'], url, get_base_headers())
    results = json.loads(data)
    tags = list(results["releases"].keys())
    return tags

def get_latest_github_release(repo: str):
    url = f"{definitions.GITHUB_API['repos']}/{repo}{definitions.GITHUB_API['releases']}{definitions.GITHUB_API['latest']}"
    headers = get_github_headers()

    data = make_request(definitions.GITHUB_API['base'], url, headers)
    return json.loads(data)

def download_compatibility_matrix():
    release_info = get_latest_github_release(definitions.FRIDA_COMPATIBILITY_MATRIX_REPO)
    assets = release_info.get("assets", [])
    json_assets = [asset for asset in assets if asset.get("name", "").endswith(".json")]

    if len(json_assets) == 0:
        raise Exception("No JSON asset found in the latest compatibility matrix release")

    matrix_url = json_assets[0]["browser_download_url"]
    parsed = urlparse(matrix_url)
    data = make_request(parsed.netloc, parsed.path, get_base_headers(), follow_redirects=True)

    with open(definitions.FRIMAN_COMPATIBILITY_MATRIX_FILE, "wb") as f:
        f.write(data)

def ensure_compatibility_matrix():
    if not file_exists(definitions.FRIMAN_COMPATIBILITY_MATRIX_FILE):
        frimanlog.info("Compatibility matrix missing, downloading it...")
        download_compatibility_matrix()

def get_compatibility_matrix():
    ensure_compatibility_matrix()

    with open(definitions.FRIMAN_COMPATIBILITY_MATRIX_FILE) as f:
        return json.load(f)

def get_compatibility_matrix_updated_at():
    if not file_exists(definitions.FRIMAN_COMPATIBILITY_MATRIX_FILE):
        return None

    updated_at = datetime.fromtimestamp(os.path.getmtime(definitions.FRIMAN_COMPATIBILITY_MATRIX_FILE))
    return updated_at.strftime("%Y-%m-%d %H:%M:%S")

def get_matching_frida_tools_version(frida_version: str):
    target_version = Version(frida_version)
    available_versions = []
    compatibility_matrix = get_compatibility_matrix()

    for version in compatibility_matrix.keys():
        try:
            available_versions.append(Version(version))
        except InvalidVersion:
            continue

    for tools_version in sorted(available_versions, reverse=True):
        matrix_entry = compatibility_matrix.get(str(tools_version), {})
        min_version = matrix_entry.get("gte")
        max_version = matrix_entry.get("lt")

        if min_version is not None and target_version < Version(min_version):
            continue

        if max_version is not None and target_version >= Version(max_version):
            continue

        return str(tools_version)

    return None

def get_github_release_assets(repo: str, tag: str):
    """Fetches release assets for a given GitHub tag."""

    url = f"{definitions.GITHUB_API['repos']}/{repo}{definitions.GITHUB_API['releases']}{definitions.GITHUB_API['tags']}/{tag}"
    headers = get_github_headers()
    
    try:
        data = make_request(definitions.GITHUB_API['base'], url, headers)
        results = json.loads(data)
    except Exception as e:
        frimanlog.error(f"Request and parsing JSON failed. {e}")
        return []
    
    return [(asset['name'], asset['browser_download_url']) for asset in results.get('assets', [])]

def get_current_config():
    if not file_exists(definitions.FRIMAN_CONFIG_FILE):
        default_config = {
            definitions.FRIMAN_CONFIG_TAGS: [],
            definitions.FRIMAN_CONFIG_UPDATED_AT: None
        }
        with open(definitions.FRIMAN_CONFIG_FILE, "w") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)

    with open(definitions.FRIMAN_CONFIG_FILE) as f:
        data = json.load(f)
        return data
    
def get_frida_tags():
    config = get_current_config()
    return config[definitions.FRIMAN_CONFIG_TAGS]

def get_config_updated_at():
    config = get_current_config()
    return config[definitions.FRIMAN_CONFIG_UPDATED_AT]

def get_installed_versions():
    installed_versions = [f for f in os.listdir(definitions.FRIMAN_ENV_FOLDER) if os.path.isdir(os.path.join(definitions.FRIMAN_ENV_FOLDER, f))]
    return installed_versions

def get_version_env_path(version: str) -> str:
    return os.path.join(definitions.FRIMAN_ENV_FOLDER, version)

def get_env_bin_path(env_path: str) -> str:
    return os.path.join(env_path, "Scripts" if os.name == "nt" else "bin")

def get_env_python_path(env_path: str) -> str:
    python_name = "python.exe" if os.name == "nt" else "python"
    return os.path.join(get_env_bin_path(env_path), python_name)

def get_env_command_path(env_path: str, command_name: str) -> str:
    suffix = ".exe" if os.name == "nt" else ""
    return os.path.join(get_env_bin_path(env_path), f"{command_name}{suffix}")

def is_version_venv(version: str) -> bool:
    env_path = get_version_env_path(version)
    return os.path.isfile(os.path.join(env_path, "pyvenv.cfg")) and os.path.isfile(get_env_python_path(env_path))

def get_current_env_path():
    symlink_path = pathlib.Path(definitions.FRIMAN_CURRENT_FOLDER)

    if symlink_path.exists():
        return str(symlink_path.resolve())
    else:
        return None

def get_current_env_python_path():
    current_env_path = get_current_env_path()
    if current_env_path is None:
        return None
    return get_env_python_path(current_env_path)

def get_current_version_in_use():
    current_env_path = get_current_env_path()

    if current_env_path is not None:
        return pathlib.Path(current_env_path).name
    else:
        return None
    
def extract_xz(input_path, delete_original=True):
    # Remove .xz extension to determine output path
    if not input_path.endswith(".xz"):
        raise ValueError("Input file must end with .xz")

    # Output is the same path without .xz
    output_path = input_path[:-3]
    output_path = os.path.abspath(output_path)

    with lzma.open(input_path, 'rb') as compressed:
        with open(output_path, 'wb') as out:
            out.write(compressed.read())

    if delete_original:
        os.remove(input_path)

    frimanlog.debug(f"Extracted to: {output_path}")
    return output_path

def is_older_than(date_string: str, days: int) -> bool:
    """
    Returns True if the given date_string is older than `days` days.
    
    date_string: a string formatted as "%Y-%m-%d %H:%M:%S"
    days: number of days to compare against
    """
    # Parse the string into a datetime object
    dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    
    # Calculate the cutoff datetime
    cutoff = datetime.now() - timedelta(days=days)
    
    # Return whether the date is older
    return dt < cutoff

"""
This module contains multiple helper function used throughout the codebase.
"""
import os
import json
import http.client
from datetime import datetime
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

    # Create the env and server folders within the above one if missing
    create_folder_if_missing(definitions.FRIMAN_ENV_FOLDER)
    create_folder_if_missing(definitions.FRIMAN_SERVER_FOLDER)

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

def make_request(host, url, headers):
    """Performs an HTTPS GET request and returns the response."""
    conn = http.client.HTTPSConnection(host)
    conn.request("GET", url, headers=headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()

    if response.status == 403:
        raise exceptions.RateLimitException(f"Status code {response.status} - error {data.decode()} - url {url}")
    elif response.status != 200:
        raise Exception(f"Status code {response.status} - error {data.decode()} - url {url}")

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
            "tags": [],
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(definitions.FRIMAN_CONFIG_FILE, "w") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)

    with open(definitions.FRIMAN_CONFIG_FILE) as f:
        data = json.load(f)
        return data
    
def get_frida_tags():
    config = get_current_config()
    return config["tags"]

def get_installed_versions():
    installed_versions = [f for f in os.listdir(definitions.FRIMAN_ENV_FOLDER) if os.path.isdir(os.path.join(definitions.FRIMAN_ENV_FOLDER, f))]
    return installed_versions
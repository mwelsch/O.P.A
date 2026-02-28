import os
import json
import platform


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPDATES_DIR = os.path.join(BASE_DIR, 'updates')
VERSION_FILE = os.path.join(BASE_DIR, 'version.json')


def get_platform():
    sys_platform = platform.system().lower()
    if sys_platform == 'windows':
        return 'windows'
    elif sys_platform == 'linux':
        return 'linux'
    elif sys_platform == 'darwin':
        return 'macos'
    return None


def get_versions():
    if not os.path.exists(VERSION_FILE):
        return {'linux': '0.0.0', 'windows': '0.0.0'}
    
    with open(VERSION_FILE, 'r') as f:
        return json.load(f)


def get_expected_version(client_platform=None):
    versions = get_versions()
    
    if client_platform is None:
        client_platform = get_platform()
    
    return versions.get(client_platform, '0.0.0')


def get_binary_path(platform_name):
    if platform_name == 'windows':
        return os.path.join(UPDATES_DIR, 'client.exe')
    elif platform_name == 'linux':
        return os.path.join(UPDATES_DIR, 'client-linux')
    elif platform_name == 'macos':
        return os.path.join(UPDATES_DIR, 'client-macos')
    return None


def check_update_required(client_version, client_platform):
    if not client_version:
        return True
    
    expected = get_expected_version(client_platform)
    
    if expected == '0.0.0':
        return False
    
    return client_version != expected


def binary_exists(platform_name):
    path = get_binary_path(platform_name)
    return path and os.path.exists(path)


def ensure_updates_dir():
    if not os.path.exists(UPDATES_DIR):
        os.makedirs(UPDATES_DIR)
        print(f"Created updates directory: {UPDATES_DIR}")

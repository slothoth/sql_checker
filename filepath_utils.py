import sys
import os
from pathlib import Path

if sys.platform == 'win32':
    import winreg


def find_steam_install():
    if sys.platform == 'win32':
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
    elif sys.platform == 'win64':
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Wow6432Node\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
    elif sys.platform == 'darwin':
        user_home = Path.home()
        steam_path = str(user_home / "Library" / "Application Support" / "Steam")
    else:
        return None
    return steam_path


def find_civ_install():
    steam_path = find_steam_install()
    if steam_path is None:
        return None
    if sys.platform == 'win32':
        civ_install = os.path.join(steam_path, "steamapps/common/Sid Meier's Civilization VII")
    elif sys.platform == 'darwin':
        civ_install = os.path.join(steam_path, "steamapps/common/Sid Meier's Civilization VII/CivilizationVII.app/Contents/Resources")
    else:
        return None
    return civ_install


def find_workshop():
    steam_path = find_steam_install()
    if steam_path is None:
        return None
    return f"{steam_path}/steamapps/workshop/content/1295660/"


def find_civ_config():
    if sys.platform == 'win32':
        local_appdata = os.getenv('LOCALAPPDATA')
        civ_config = f"{local_appdata}/Firaxis Games/Sid Meier's Civilization VII"
    elif sys.platform == 'darwin':
        user_home = Path.home()
        civ_config = str(user_home / "Library" / "Application Support" / "Civilization VII")
    else:
        return None
    return civ_config

import os
from pathlib import Path
import sys
if sys.platform == 'win32':
    import winreg


class FilePaths:
    def __init__(self):
        self.civ_config = self._find_civ_config()
        self.civ_install = self._find_civ_install()
        self.workshop = self._find_workshop()

    @staticmethod
    def _find_steam_install():
        if sys.platform == 'win32':
            win_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam")
            steam_path, _ = winreg.QueryValueEx(win_key, "SteamPath")
        elif sys.platform == 'win64':
            win_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Wow6432Node\Valve\Steam")
            steam_path, _ = winreg.QueryValueEx(win_key, "SteamPath")
        elif sys.platform == 'darwin':
            user_home = Path.home()
            steam_path = str(user_home / "Library" / "Application Support" / "Steam")
        else:
            return None
        return steam_path

    def _find_civ_install(self):
        steam_path = self._find_steam_install()
        if steam_path is None:
            return None
        if sys.platform == 'win32':
            civ_install = os.path.join(steam_path, "steamapps/common/Sid Meier's Civilization VII")
        elif sys.platform == 'darwin':
            civ_install = os.path.join(steam_path,
                                       "steamapps/common/Sid Meier's Civilization VII/CivilizationVII.app/Contents/Resources")
        else:
            return None
        return civ_install

    def _find_workshop(self):
        steam_path = self._find_steam_install()
        if steam_path is None:
            return None
        return f"{steam_path}/steamapps/workshop/content/1295660/"

    @staticmethod
    def _find_civ_config():
        if sys.platform == 'win32':
            local_appdata = os.getenv('LOCALAPPDATA')
            civ_config = f"{local_appdata}/Firaxis Games/Sid Meier's Civilization VII"
        elif sys.platform == 'darwin':
            user_home = Path.home()
            civ_config = str(user_home / "Library" / "Application Support" / "Civilization VII")
        else:
            return None
        return civ_config


LocalFilePaths = FilePaths()

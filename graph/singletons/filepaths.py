import os
from pathlib import Path
from platformdirs import user_data_dir
import logging
from logging.handlers import RotatingFileHandler
import sys
if sys.platform == 'win32':
    import winreg



class FilePaths:
    def __init__(self):
        self.save_appdata_path = self.setup_appdata(civ_type='CivVII')               #  for when we include VI
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

    @staticmethod
    def setup_appdata(civ_type):
        app_name = 'CivSQLChecker'
        save_appdata_path = user_data_dir(civ_type, app_name)
        os.makedirs(save_appdata_path, exist_ok=True)
        base_dir = Path(save_appdata_path)
        folders = ["db_spec", "mined", "unused", "logs"]
        for folder in folders:
            folder_path = base_dir / folder
            folder_path.mkdir(parents=True, exist_ok=True)
        return save_appdata_path

    def app_data_path_form(self, filename):
        file_path = os.path.join(self.save_appdata_path, filename)
        return file_path


LocalFilePaths = FilePaths()

# logger setup

logger = logging.getLogger("SQLCheckerLogger")
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

info_handler = logging.handlers.RotatingFileHandler(Path(LocalFilePaths.app_data_path_form('logs')) / "app.log",
                                                    maxBytes=1_000_000, backupCount=5)
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(formatter)

error_handler = logging.handlers.RotatingFileHandler(Path(LocalFilePaths.app_data_path_form('logs')) / "errors.log",
                                                     maxBytes=1_000_000, backupCount=5)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()       # terminal only
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

if logger.hasHandlers():
    logger.handlers.clear()

logger.addHandler(info_handler)
logger.addHandler(error_handler)
logger.addHandler(console_handler)

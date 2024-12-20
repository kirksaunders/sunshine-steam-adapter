import os
import re
import win32con, win32gui
import winreg
from pathlib import Path
from typing import Any, List
from util.game import *

def read_reg_value(key, value_key: str) -> Any:
    value, _ = winreg.QueryValueEx(key, value_key)
    return value

def get_steam_install_path() -> Path:
    with winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Valve\Steam', 0, winreg.KEY_READ) as key:
        return Path(read_reg_value(key, 'SteamPath'))

def get_localization_entry(key: str) -> str | None:
    language = get_steam_language()
    localization_file_path = get_steam_install_path() / "steamui" / "localization" / f"steamui_{language}-json.js"
    if not localization_file_path.is_file():
        raise FileNotFoundError(f"Could not find steam localization file at {localization_file_path}")

    value_pattern = re.compile(r'"' + re.escape(key) + r'":"([^"\\]*(\\.[^"\\]*)*)"')
    with localization_file_path.open(encoding="utf-8") as localization_file:
        value_match = value_pattern.search(localization_file.read())
        if value_match:
            return value_match.group(1).replace("\\'", "'")

    return None

def get_steam_language() -> str:
    with winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Valve\Steam', 0, winreg.KEY_READ) as key:
        return read_reg_value(key, 'Language')

def get_steam_config_path() -> Path:
    with winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Valve\Steam\ActiveProcess', 0, winreg.KEY_READ) as key:
        return get_steam_install_path() / 'userdata' / str(read_reg_value(key, 'ActiveUser')) / 'config'

def get_big_picture_window() -> int:
    title = get_localization_entry('SP_WindowTitle_BigPicture')
    if not title:
        raise ValueError('Failed to find Big Picture mode window title in localization file')

    return win32gui.FindWindow('SDL_app', title)

def get_steam_window() -> int:
    return win32gui.FindWindow('SDL_app', 'Steam')

def close_big_picture():
    handle = get_big_picture_window()
    if handle:
        win32gui.SendMessage(handle, win32con.WM_CLOSE)

def close_steam_window():
    handle = get_steam_window()
    if handle:
        win32gui.SendMessage(handle, win32con.WM_CLOSE)

def get_installed_steam_games() -> List[Game]:
    installed = []
    with winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Valve\Steam\Apps', 0, winreg.KEY_READ) as root_key:
        subkey_count, _, _ = winreg.QueryInfoKey(root_key)
        for i in range(subkey_count):
            game_id = winreg.EnumKey(root_key, i)
            with winreg.OpenKeyEx(root_key, game_id) as game_key:
                try:
                    game_name = read_reg_value(game_key, 'Name')
                    game = Game(game_id, game_name)
                    if read_reg_value(game_key, 'Installed'):
                        installed.append(game)
                    else:
                        print(f"Game {game} isn't installed. Skipping.")
                except FileNotFoundError as e:
                    print(f"Game id={game_id} either doesn't have name, or installed flag. Skipping.")
    return installed

# Expose the steam config path as a constant value so it can be used without re-computing it
STEAM_CONFIG_PATH = get_steam_config_path()

# The following function is adapted from code originally from https://github.com/boppreh/steamgrid.
# Please refer to the below license from the original code.

# The MIT License (MIT)

# Copyright (c) 2016 BoppreH

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

def get_non_steam_games() -> List[Game]:
    shortcut_path = STEAM_CONFIG_PATH / 'shortcuts.vdf'
    if not shortcut_path.is_file():
        print(f"No non-steam games shortcut file found at {shortcut_path}. Assuming no non-steam games are installed.")
        return []
    shortcut_bytes = shortcut_path.read_bytes()

	# The actual binary format is known, but using regexes is way easier than
	# parsing the entire file. If I run into any problems I'll replace this.
    game_pattern = re.compile(b"(?i)\x00\x02appid\x00(.{4})\x01appname\x00([^\x08]+?)\x00\x01exe\x00([^\x08]+?)\x00\x01.+?\x00tags\x00(?:\x01([^\x08]+?)|)\x08\x08")
    games = []
    for game_match in game_pattern.findall(shortcut_bytes):
        id = str(int.from_bytes(game_match[0], byteorder='little', signed=False))
        name = game_match[1].decode('utf-8')
        target = game_match[2].decode('utf-8')
        target_process = os.path.basename(re.sub(r'^"|"$', '', target))
        games.append(Game(id="unknown", name=name, alt_id=id, process_name=target_process))

    return games

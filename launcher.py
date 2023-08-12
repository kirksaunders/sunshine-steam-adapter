import argparse
import os
import subprocess
import time
import win32com.client, win32gui
import winreg
from typing import Callable, Optional
from util.log import *
from util.steam import *

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
LOG = Logger(os.path.join(SCRIPT_DIR, 'logs', 'launcher-log.txt'))

def get_running_processes():
    WMI = win32com.client.GetObject('winmgmts:')
    processes = WMI.InstancesOf('Win32_Process')
    map = {}
    for process in processes:
        map[process.Properties_("Name").Value] = process.Properties_("ProcessID").Value
    return map

def wait_for_state_with_timeout(state_checker: Callable[[], bool], timeout: float):
    start_time = time.perf_counter()
    while not state_checker():
        if time.perf_counter() - start_time > timeout:
            raise RuntimeError(f"Timed out waiting for previous step to finish. Waited {timeout} seconds")
        time.sleep(0.25)

def launch_game_and_wait_for_close(game_id: Optional[int] = None, process_name: Optional[str] = None):
    """Launch big picture mode, launch steam game by id, then wait for the game to quit.

    By default, this will use Steam's registry keys to detect when the game quits. However, the registry key is
    not set for non-steam games. Therefore, you must supply the process_name argument when launching non-steam
    games. The process name will be used to detect once the non-steam game has quit running.

    If you don't provide a game id, only big picture mode is launched. The stream ends once big picture mode is
    closed.
    """

    LOG.log(f"Starting launcher with args game_id={game_id}, process_name={process_name}")

    with winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Valve\Steam', 0, winreg.KEY_READ) as key:
        # Get steam executable path
        steam_path = read_reg_value(key, 'SteamExe')

        # Launch steam if it's not already running
        if not os.path.basename(steam_path) in get_running_processes():
            LOG.log("Launching Steam, since it was not already running")
            subprocess.Popen(steam_path)

            # Wait for steam window to show. That's how we know it has fully started
            def is_steam_window_visible():
                handle = win32gui.FindWindow('SDL_app', 'Steam')
                return handle != 0 and win32gui.IsWindowVisible(handle)
            wait_for_state_with_timeout(is_steam_window_visible, 15)
            LOG.log("Started Steam")

            # Give a little bit more buffer before starting big picture mode
            time.sleep(0.5)

        # Start big picture mode
        LOG.log("Opening Steam big picture mode")
        subprocess.run([steam_path, 'steam://open/bigpicture'])

        # Wait for big picture mode to open
        def is_big_picture_mode_open():
            handle = get_big_picture_window()
            return handle != 0 and win32gui.IsWindowVisible(handle)
        wait_for_state_with_timeout(is_big_picture_mode_open, 15)
        LOG.log("Opened Steam big picture mode")

        # Give a little bit more buffer before starting the game
        time.sleep(1)

        if game_id:
            # Launch game
            LOG.log(f"Launching game with id={game_id}")
            subprocess.run([steam_path, f"steam://rungameid/{game_id}"])

            def is_game_running() -> bool:
                if process_name:
                    return process_name in get_running_processes()
                else:
                    return read_reg_value(key, 'RunningAppId') == game_id

            # Wait for game to start running
            wait_for_state_with_timeout(is_game_running, 15)
            LOG.log("Game is now running")

            # Wait for game to close
            LOG.log("Waiting for game to quit")
            while is_game_running():
                time.sleep(0.25)
            LOG.log("Game has quit")

            # Let teardown script handle closing Steam big picture. This is to prevent the stream from showing the desktop briefly
        else:
            # Wait for big picture mode to close
            LOG.log("Waiting for Steam big picture mode to close")
            while is_big_picture_mode_open():
                time.sleep(0.25)
            LOG.log("Steam big picture mode has closed, finishing up")

def main():
    parser = argparse.ArgumentParser(
        prog='Sunshine Steam Adapater Launcher',
        description='This is a launcher for steam games, for use with Nvidia Gamestream/Sunshine. It handles launching of a steam game based on its ID.'
    )
    parser.add_argument('-g', '--game_id', type=int, help='The steam game id to launch. If not specified, steam big picture mode will be launched.')
    parser.add_argument('-p', '--process_name', type=str, required=False,
                        help='If the game to launch is a non-steam game, you must supply the process name here. For example, any games that run via retroarch, you should specify retroarch.exe. If you provide this argument, you must also provide the game_id argument.')
    args = parser.parse_args()

    if args.process_name and not args.game_id:
        raise ValueError("game_id must be provided if process_name is provided. Run with `--help` flag for more info.")

    launch_game_and_wait_for_close(game_id=args.game_id, process_name=args.process_name)

if __name__ == '__main__':
    LOG.with_error_catching(main, 'launcher script')

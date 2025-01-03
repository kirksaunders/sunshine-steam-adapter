import argparse
import subprocess
import time
import win32com.client, win32gui
import winreg
from pathlib import Path
from typing import Callable, Optional
from util.log import *
from util.steam import *

SCRIPT_DIR = Path(__file__).parent
LOG = Logger(SCRIPT_DIR / 'logs' / 'launcher-log.txt')

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
    """Launch steam game by id, then wait for the game to quit.

    By default, this will use Steam's registry keys to detect when the game quits. However, the registry key is
    not set for non-steam games. Therefore, you must supply the process_name argument when launching non-steam
    games. The process name will be used to detect once the non-steam game has quit running.

    If you don't provide a game id, the stream ends once big picture mode is closed.
    """

    LOG.log(f"Starting launcher with args game_id={game_id}, process_name={process_name}")

    # Get steam executable path
    steam_path = get_steam_exe_path()

    if game_id:
        # Launch game
        LOG.log(f"Launching game with id={game_id}")
        subprocess.run([steam_path, f"steam://rungameid/{game_id}"])

        with winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Valve\Steam', 0, winreg.KEY_READ) as key:
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
        def is_big_picture_mode_open():
            handle = get_big_picture_window()
            return handle != 0 and win32gui.IsWindowVisible(handle)
        while is_big_picture_mode_open():
            time.sleep(0.25)
        LOG.log("Steam big picture mode has closed, finishing up")

def main():
    parser = argparse.ArgumentParser(
        prog='Sunshine Steam Adapater Launcher',
        description='This is a launcher for steam games, for use with Sunshine. It handles launching of a steam game based on its ID.'
    )
    parser.add_argument('-g', '--game_id', type=int, help='The steam game id to launch. If not specified, nothing will be launched, and the script will exit once big picture mode is closed.')
    parser.add_argument('-p', '--process_name', type=str, required=False,
                        help='If the game to launch is a non-steam game, you must supply the process name here. For example, any games that run via retroarch, you should specify retroarch.exe. If you provide this argument, you must also provide the game_id argument.')
    args = parser.parse_args()

    if args.process_name and not args.game_id:
        raise ValueError("game_id must be provided if process_name is provided. Run with `--help` flag for more info.")

    launch_game_and_wait_for_close(game_id=args.game_id, process_name=args.process_name)

if __name__ == '__main__':
    LOG.with_error_catching(main, 'launcher script')

import argparse
import os
import subprocess
import time
import win32com.client, win32gui
import winreg
from typing import Callable, Optional
from util.steam import *

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
            print("Previous step failed. Attempting to close Steam big picture mode and stopping execution")
            close_big_picture()
            exit(-1)
        time.sleep(0.25)

def launch_game_and_wait_for_close(game_id: Optional[int] = None, process_name: Optional[str] = None):
    """Launch big picture mode, launch steam game by id, wait for the game to quit, then close big picture mode.

    By default, this will use Steam's registry keys to detect when the game quits. However, the registry key is
    not set for non-steam games. Therefore, you must supply the process_name argument when launching non-steam
    games. The process name will be used to detect once the non-steam game has quit running.

    If you don't provide a game id, only big picture mode is launched. The stream ends once big picture mode is
    closed.
    """

    with winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Valve\Steam', 0, winreg.KEY_READ) as key:
        # Get steam executable path
        steam_path = read_reg_value(key, 'SteamExe')

        # Launch steam if it's not already running
        if not os.path.basename(steam_path) in get_running_processes():
            print("Launching Steam, since it was not already running")
            subprocess.Popen(steam_path)

            # Wait for steam window to show. That's how we know it has fully started
            wait_for_state_with_timeout(lambda: win32gui.FindWindow('SDL_app', 'Steam') != 0, 15)
            print("Started Steam")

            # Give a little bit more buffer before starting big picture mode
            time.sleep(1)

        # Start big picture mode
        print("Opening Steam big picture mode")
        subprocess.run([steam_path, 'steam://open/bigpicture'])

        # Wait for big picture mode to open
        wait_for_state_with_timeout(lambda: win32gui.FindWindow('SDL_app', 'Steam Big Picture Mode') != 0, 15)
        print("Opened Steam big picture mode")

        # Give a little bit more buffer before starting the game
        time.sleep(1)

        if game_id:
            # Launch game
            print(f"Launching game with id={game_id}")
            subprocess.run([steam_path, f"steam://rungameid/{game_id}"])

            def is_game_running() -> bool:
                if process_name:
                    return process_name in get_running_processes()
                else:
                    return read_reg_value(key, 'RunningAppId') == game_id

            # Wait for game to start running
            wait_for_state_with_timeout(is_game_running, 15)
            print("Game is now running")

            # Wait for game to close
            print("Waiting for game to quit")
            while is_game_running():
                time.sleep(0.25)
            print("Game has quit")

            # Close steam big picture mode
            print("Closing Steam big picture mode and finishing up")
            close_big_picture()
        else:
            # Wait for big picture mode to close
            print("Waiting for Steam big picture mode to close")
            while win32gui.FindWindow('SDL_app', 'Steam Big Picture Mode') != 0:
                time.sleep(0.25)
            print("Steam big picture mode has closed, finishing up")

if __name__ == '__main__':
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

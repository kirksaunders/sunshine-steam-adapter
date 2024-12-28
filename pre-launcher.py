import subprocess
import time
import win32com.client, win32gui
import win32process
from pathlib import Path
from typing import Callable
from util.log import *
from util.steam import *

SCRIPT_DIR = Path(__file__).parent
LOG = Logger(SCRIPT_DIR / 'logs' / 'pre-launcher-log.txt')

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

def launch_steam():
    """Ensure steam is running, then open big picture mode."""

    # Get steam executable path
    steam_path = get_steam_exe_path()

    # Launch steam if it's not already running
    if not steam_path.name in get_running_processes():
        LOG.log("Launching Steam, since it was not already running")
        subprocess.Popen(steam_path, creationflags=win32process.DETACHED_PROCESS)

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

    # Wait for big picture mode to open. We require it to signal as open a few
    # times in a row, since it will sometimes close and reopen randomly.
    open_count = 0
    def is_big_picture_mode_open():
        nonlocal open_count
        handle = get_big_picture_window()
        if handle != 0 and win32gui.IsWindowVisible(handle):
            open_count += 1
        else:
            open_count = 0
        return open_count >= 6
    wait_for_state_with_timeout(is_big_picture_mode_open, 15)
    LOG.log("Opened Steam big picture mode")

def main():
    launch_steam()

if __name__ == '__main__':
    LOG.with_error_catching(main, 'pre-launcher script')

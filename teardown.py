import argparse
import subprocess
import sys
import time
import win32api, win32com.client, win32con, win32process
import winreg
from util.log import *
from util.steam import *

SCRIPT_DIR = Path(__file__).parent
LOG = Logger(SCRIPT_DIR / 'logs' / 'teardown-log.txt')

def terminate_recursive(pid: int):
    wmi = win32com.client.GetObject('winmgmts:')
    children = wmi.ExecQuery(f"Select * from win32_process where ParentProcessId={pid}")
    for child in children:
        terminate_recursive(child.Properties_('ProcessID').Value)
    handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ | win32con.PROCESS_TERMINATE, False, pid)
    name = win32process.GetModuleFileNameEx(handle, 0)
    win32api.TerminateProcess(handle, 0)
    win32api.CloseHandle(handle)
    LOG.log(f"Killed process with exe={name} and id={pid}")

def normal_handler():
    LOG.log('Teardown script running in normal mode')

    # Wait a second after main launcher has finished. This is done for two reasons:
    # 1. To let the stream shut down prior to closing big picture mode. We don't want the desktop to flash on the stream.
    # 2. To give the game a little bit more of a chance to terminate on its own, before we forcibly do it.
    time.sleep(1)

    # Kill the game process (should ideally be terminated already)
    with winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Valve\Steam\ActiveProcess', 0, winreg.KEY_READ) as key:
        steam_pid = read_reg_value(key, 'pid')

        if steam_pid:
            # Kill any child processes of steam. This is the only way to close the game, considering we don't know its process name
            wmi = win32com.client.GetObject('winmgmts:')
            children = wmi.ExecQuery(f"Select * from win32_process where ParentProcessId={steam_pid}")
            for child in children:
                if child.Name != 'steamwebhelper.exe' and child.Name != 'GameOverlayUI.exe':
                    LOG.log(f"Attempting to kill process with pid={child.Properties_('ProcessID').Value} and all of its children")
                    terminate_recursive(child.Properties_('ProcessID').Value)

    # Close big picture mode (should ideally be closed already)
    LOG.log("Closing Steam big picture mode")
    close_big_picture()
    LOG.log("Closed Steam big picture mode")

    def is_steam_window_visible():
        handle = get_steam_window()
        return handle != 0 and win32gui.IsWindowVisible(handle)

    # Wait for Steam regular window to open. At most wait for 10 seconds
    LOG.log("Waiting for regular Steam window to open")
    start_time = time.perf_counter()
    while not is_steam_window_visible() and time.perf_counter() - start_time < 10:
        time.sleep(0.25)

    # Close Steam regular window. Unfortunately haven't found a better way to do this. Steam seems to try opening the window multiple times
    LOG.log("Attempting to close regular Steam window")
    is_closed_count = 0
    # Require the window to report as closed 8 times in a row before we quit. But just give up after 10 seconds
    start_time = time.perf_counter()
    while is_closed_count < 8 and time.perf_counter() - start_time < 10:
        if not is_steam_window_visible():
            is_closed_count += 1
        else:
            is_closed_count = 0
        LOG.log("Sending close signal to Steam window")
        close_steam_window()
        time.sleep(0.5)
    LOG.log("Closed regular Steam window")
    LOG.log("Teardown finished")

def detached_handler():
    LOG.log('Teardown script running in detached mode')
    # Spawn background process to close regular Steam window. This will avoid us blocking stream shutdown
    subprocess.Popen([sys.executable, __file__, 'normal'], creationflags=win32process.DETACHED_PROCESS)
    LOG.log('Spawned background process to do actual teardown')

def main():
    parser = argparse.ArgumentParser(
        prog='Sunshine Steam Adapater Teardown Script',
        description='This script is used to terminate any running Steam games, close big picture mode, and the regular Steam window.'
    )
    subparsers = parser.add_subparsers(required=True, help='What action to take.')

    normal_parser = subparsers.add_parser('normal', help='Normal cleanup mode. Will terminate any Steam games, close big picture mode, and close the normal Steam window.')
    normal_parser.set_defaults(handler=normal_handler)

    detached_parser = subparsers.add_parser('detached', help='Detached cleanup mode. Will spawn detached process to do cleanup. This is so the stream isn\'t blocked on waiting for shutdown.')
    detached_parser.set_defaults(handler=detached_handler)

    args = parser.parse_args()
    args.handler()

if __name__ == '__main__':
    LOG.with_error_catching(main, 'teardown script')
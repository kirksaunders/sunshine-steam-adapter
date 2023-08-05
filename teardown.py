import os
import time
import win32con, win32com.client, win32gui
import winreg

def close_big_picture():
    handle = win32gui.FindWindow('SDL_app', 'Steam Big Picture Mode')
    if handle:
        win32gui.SendMessage(handle, win32con.WM_CLOSE)

# Check if game is still running
with winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Valve\Steam', 0, winreg.KEY_READ) as key:
    running_app, _ = winreg.QueryValueEx(key, 'RunningAppID')

    if not running_app:
        exit(0)

    # Wait for a little bit after main launcher has finished, to see if app closes on its own
    time.sleep(2.5)

    if running_app:
        with winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Valve\Steam\ActiveProcess', 0, winreg.KEY_READ) as key:
            steam_pid, _ = winreg.QueryValueEx(key, 'pid')

            if steam_pid:
                # Kill any child processes of steam. This is the only way to close the game, considering we don't know its process name
                wmi = win32com.client.GetObject('winmgmts:')
                children = wmi.ExecQuery(f"Select * from win32_process where ParentProcessId={steam_pid}")
                for child in children:
                    if child.Name != 'steamwebhelper.exe' and child.Name != 'GameOverlayUI.exe':
                        print(f"Killing process with name={child.Name} and id={child.Properties_('ProcessID').Value}")
                        os.system(f"taskkill /F /T /pid {child.Properties_('ProcessID').Value}")

            # Close big picture mode
            close_big_picture()
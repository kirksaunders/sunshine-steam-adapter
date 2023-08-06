import os
import time
import win32com.client
import winreg
from util.steam import *

# Wait for a second after main launcher has finished, to see if app closes on its own
time.sleep(1)

with winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Valve\Steam\ActiveProcess', 0, winreg.KEY_READ) as key:
    steam_pid = read_reg_value(key, 'pid')

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
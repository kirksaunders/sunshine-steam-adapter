# Details
This package contains tools to automatically add your Steam games to your Sunshine (or Nvidia Gamestream) library. The main features are:
- Automatic detection of Steam games.
- Automatic* detection of non-Steam games. *They are detected automatically, but must be added using the installer, one-by-one. This is because you must provide the Steam game id for the non-steam game.
- Automatic sychronization of artwork. This includes custom artwork (see https://www.steamgriddb.com/boop), even for non-steam games.

Below are more details for how games added to Sunshine through this tool will be handled:
- Steam is launched if not already running.
- Games are launched in big picture mode. 
- The wrapper detects when the game has ended, and will end the stream.
- If the stream ends before the game ends, the game is terminated.
- Once the stream/game ends, big picture mode is closed.

The installer will also automatically install Steam Big Picture Mode as a game in Sunshine. When launched, it will start Steam and launch Big Picture Mode. The stream will automatically end if you close Big Picture Mode.

**Warning:** Sunshine currently has a bug (https://github.com/LizardByte/Sunshine/issues/1456) that causes prep commands to fail after so many runs. The only solution is to restart Sunshine on your host PC. This tool uses prep commands, and is therefore affected. There's a workaround posted in the Sunshine issue, if you're interested.

# Compatibility
Only Windows hosts are supported. The launcher relies heavily on registry keys that Steam writes. In theory, these registries also exist on Linux, but reading them would require maintaing two code paths. Contributions are welcome.

Both Sunshine and Nvidia Gamestream hosts are supported. However, Sunshine is better supported, since it can properly detect when the game has been quit.

# Usage
## Setup
1. Install python 3.11 or higher. Ensure that any files with `.py` extension are configured to run with python.
2. Clone (or download and extract) this repo. Keep it in a consistent place, where it won't be deleted/moved.
3. Install the required pip packages by running `python3 -m pip install -r requirements.txt` from this repo root.

## Installer
Most users will only be interested in the installer script, which provides an interactive menu for syncing your Steam library with Sunshine/Nvidia Gamestream. The general usage pattern of `installer.py` is as follows:
1. Ensure Steam is running, and you are logged in to your Steam account.
2. Run installer with `python3 installer.py` or `./installer.py`.
3. The installer will automatically load all of your installed official steam games.
4. If you have previously run the script, your previous state will be loaded. This includes any non-steam games that you have added, and any official steam games that you have explicitly removed from your Sunshine/Gamestream library.
5. If any of your non-steam games have changed name, those changes will be detected. If any non-steam games have been removed from steam, you will be prompted to remove them from your Sunshine/Gamestream library.
6. Follow the menu prompts to make any changes to your library. You can remove official steam games, add non-steam games, etc.
7. After you have finished making changes, you must choose a menu option to apply to Sunshine/Nvidia Gamestream.
    1. If using Nvidia Gamestream, you must choose the menu option to create batch shortcuts. The shortcuts will be saved to your directory of choosing. You must manually add each shortcut to Nvidia Gamestream via Nvidia GeForce Experience settings.
    2. If using Sunshine, you must choose the menu option to write to a Sunshine config file. The default save location is the system-wide Sunshine config file. This file requires admin access to modify by default. So, either modify its permissions to allow your user to modify it, or run this script as administrator, or write to a different location and copy over to the protected file manually. **Warning: The existing contents of your config file are not preserved. If you want to maintain your existing Sunshine games, save to a different location, then merge the two manually.**
8. Quit the script. Your changes are automatically saved. The next time you run the script, it will remember your non-steam games and which games you have explicitly removed from your library.

**Important:** If you move/rename/remove your local checkout of this git repository, any games you've added to Sunshine will stop working. You must keep this repository around.

## Launcher
Advanced users may be interested in using the launcher script directly. This launcher is a wrapper around Steam's `steam://rungame/<app-id>` API. It will ensure the game is launched in big picture mode, and will block until the game terminates. It also supports non-steam games (although it requires an extra parameter to track when the game ends).

For usage, run `python3 launcher.py --help`. You can also read the source of `launcher.py` (it's well-commented) to see what exactly it's doing.

## Teardown
Similarly to the launcher script, there's a teardown script. This teardown script will ensure that the game is terminated after the stream ends. This is only relevant for Sunshine, since Nvidia Gamestream doesn't provide an ability to run scripts after the stream ends. This script will check if any steam game is running after the stream ends. If there is, it will kill any child processes of Steam. Advanced users: read source of `teardown.py` for more details.

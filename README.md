# Details
This package contains tools to automatically add your Steam games to your [Sunshine](https://app.lizardbyte.dev/Sunshine) library. The main features are:
- Automatic detection of both official Steam games, and non-Steam games within your Steam library.
- Automatic sychronization of artwork. This includes custom artwork (see https://www.steamgriddb.com/boop), even for non-steam games.
- Automatic* synchronization of game settings. Any changes to game settings you make while streaming will be saved and restored the next time you stream. But, they do not persist outside of streams. This is done on a per-client basis (based on client resolution). This is particularly useful for setting the game's exclusive fullscreen resolution to match the streaming resolution. *The synchronization process is done automatically, but the feature is opt-in for each game. You must provide the path to the game's settings file.

Below are more details for how games added to Sunshine through this tool will be launched when selected within Sunshine:
- If the game has settings sync enabled, and a saved settings file is found, it is loaded.
- Steam is launched if not already running.
- Games are launched in big picture mode.
- The wrapper detects when the game has ended, and will end the stream.
- If the stream ends before the game ends, the game is terminated.
- Once the stream/game ends, big picture mode is closed.
- If the game has settings sync enabled, the settings changes made during the stream are saved. The original settings (before streaming) are restored.

The installer will also automatically install Steam Big Picture Mode as a game in Sunshine. When launched, it will start Steam and launch Big Picture Mode. The stream will automatically end if you close Big Picture Mode.

# Compatibility
Only Windows hosts are supported. The launcher relies heavily on registry keys that Steam writes. In theory, these registries also exist on Linux, but reading them would require maintaing two code paths. Contributions are welcome.

Only Sunshine (and not Nvidia Gamestream) is supported. You could technically create a shortcut file or batch script that uses the launcher script with Nvidia Gamestream, but you won't get any of the automatic stream termination when the game closes. And when it comes down to it, Nvidia Gamestream is EOL anyways, and any support in this utility would go largely untested.

# Usage
## Setup
1. Install python 3.11 or higher. Ensure that any files with `.py` extension are configured to run with python.
2. Clone (or download and extract) this repo. Keep it in a consistent place, where it won't be deleted/moved.
3. Install the required pip packages by running `python3 -m pip install -r requirements.txt` from this repo root.

## Installer
Most users will only be interested in the installer script, which provides an interactive menu for syncing your Steam library with Sunshine. The general usage pattern of `installer.py` is as follows:
1. Ensure Steam is running, and you are logged in to your Steam account.
2. Run installer with `python3 installer.py` or `./installer.py`.
3. The installer will automatically load all of your installed official steam games, and any non-steam games in your steam library.
4. If you have previously run the script, your previous state will be loaded. This includes any non-steam games that you have added, and any official steam games that you have explicitly removed from your Sunshine library.
5. If any of your games have changed name, those changes will be detected. If any games have been removed/uninstalled from Steam, you will be prompted to remove them from your Sunshine library.
6. Follow the menu prompts to make any changes to your library. You can remove games, configure settings sync, etc.
7. After you have finished making changes, you must choose the menu option to apply to Sunshine.
    1. The default save location is the system-wide Sunshine config file. This file requires admin access to modify by default. So, either modify its permissions to allow your user to modify it, or run this script as administrator, or write to a different location and copy over to the protected file manually. **Warning: The existing contents of your config file are not preserved. If you want to maintain your existing Sunshine games, save to a different location, then merge the two manually.**
8. Quit the script. Your changes are automatically saved. The next time you run the script, it will remember your non-steam games and which games you have explicitly removed from your library.

**Important:** If you move/rename/remove your local checkout of this git repository, any games you've added to Sunshine will stop working. You must keep this repository around.

### Troubleshooting
If you see `Game id=<game id> either doesn't have name, or installed flag. Skipping.` for a Steam game that you expect to be working, then try launching the game through Steam, letting it load, then quitting it. Afterwards, try running the installer script again. Steam doesn't write all registry keys until the game has been launched at least once.

## Launcher
Advanced users may be interested in using the launcher script directly. This launcher is a wrapper around Steam's `steam://rungame/<app-id>` API. It will launch the game, then block until the game terminates. It also supports non-steam games (although it requires an extra parameter to track when the game ends).

For usage, run `python3 launcher.py --help`. You can also read the source of `launcher.py` (it's well-commented) to see what exactly it's doing.

## Pre-Launcher
Before the launcher is run, you likely want to run the pre-launcher script. This script will start steam if it's not already running, then open big picture mode.

For usage, run `python3 pre-launcher.py --help`. Reading the source is also recommended.

## Teardown
Similarly to the launcher script, there's a teardown script. This teardown script will ensure that the game is terminated after the stream ends. It does this by killing all non-official child processes of Steam. Advanced users: read source of `teardown.py` for more details.

## Settings Sync
Included is also a settings synchronization script. This script will allow you to make settings changes in your games specifically for each stream resolution. These settings will only apply when streaming to that same stream resolution. The script has two modes: load and save.

Load mode:
1. Backs up the current game settings to a backup file. These settings represent the non-streaming settings.
2. If a saved settings file exists for the given game id, it is loaded to the game.

Save mode:
1. Saves the current game settings file to the save file based on the running game and current stream resolution.
2. Restores the backup of the settings file, if it exists (should have been created by load mode).
3. Deletes the settings file backup, since we just restored it.

Advanced users: read source of `settings-sync.py` for more details.

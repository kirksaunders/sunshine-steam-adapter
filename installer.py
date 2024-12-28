import json
import traceback
from pathlib import Path
from util.io import *
from util.library import *
from util.steam import *

SCRIPT_DIR = Path(__file__).parent
PRE_LAUNCHER_PATH = SCRIPT_DIR / 'pre-launcher.py'
LAUNCHER_PATH = SCRIPT_DIR / 'launcher.py'
TEARDOWN_PATH = SCRIPT_DIR / 'teardown.py'
SETTINGS_SYNC_PATH = SCRIPT_DIR / 'settings-sync.py'
LIBRARY_CACHE = SCRIPT_DIR / ".library-cache"
ART_CACHE_DIR = SCRIPT_DIR / ".converted-artwork-cache"
STATIC_ART_DIR = SCRIPT_DIR / "static-artwork"
DEFAULT_SHORTCUT_DIR = SCRIPT_DIR / 'shortcuts'
DEFAULT_SUNSHINE_CONFIG_PATH = Path(r'C:\Program Files\Sunshine\config\apps.json')

def configure_non_steam_game(library: Library):
    print(f"There are currently {len(library.get_non_steam_games())} non-steam games in your library:")
    games = Library.select_games('Input the number of the game(s) to add: ',
                                 "Are you sure you'd like to configure the above games?",
                                 library.get_non_steam_games())
    for game in games:
        print(f"Configuring {game}...")
        process_name = input(f"Input the process name to track run status (press enter to keep current value of {game.process_name}): ")
        if process_name != '':
            game.process_name = process_name
        library.to_file(LIBRARY_CACHE)
        print(f"Successfully configured {game}.")
        newline()
    print(f"Configured {len(games)} non-steam games.")

def remove_game(library: Library):
    print(f"There are currently {len(library.get_games())} games in your library:")
    games = Library.select_games('Input the number of the game(s) to remove: ',
                                 "Are you sure you'd like to remove the above games?",
                                 library.get_games())
    for game in games:
        library.remove_game(game)
        library.to_file(LIBRARY_CACHE)
        print(f"Removed {game} from library.")
    newline()
    print(f"Removed {len(games)} games.")

def remove_exclusion(library: Library):
    print(f"There are currently {len(library.get_exclusions())} games previously removed from the library:")
    games = Library.select_games('Input the number of the game(s) to return to your library: ',
                                 "Are you sure you'd like to return the above games to your library?",
                                 library.get_exclusions())
    for game in games:
        library.remove_exclusion(game)
        library.to_file(LIBRARY_CACHE)
        print(f"Added {game} back to library.")
    newline()
    print(f"Returned {len(games)} games to your library.")

def configure_game_settings_sync(library: Library):
    print(f"There are currently {len(library.get_games())} games in your library:")
    games = Library.select_games('Input the number of the game(s) to configure settings sync for: ',
                                 "Are you sure you'd like to configure settings sync for the above games?",
                                 library.get_games())
    for game in games:
        print(f"Configuring settings sync for {game}...")
        if game.settings_path:
            if yes_or_no(f"Settings sync already enabled for {game} with settings file {game.settings_path}. Would you like to disable it?"):
                game.settings_path = None
                library.to_file(LIBRARY_CACHE)
                print(f"Disabled settings sync for {game}.")
                continue

        settings_path_input = input(f"Input the path to the game's settings file{f' ({game.settings_path})' if game.settings_path else ''}: ")
        settings_path = Path(game.settings_path if game.settings_path and settings_path_input == '' else settings_path_input)
        if not settings_path.is_file():
            print(f"Error: No file {settings_path} exists.")
            return
        game.settings_path = settings_path.resolve()
        library.to_file(LIBRARY_CACHE)
        print(f"Enabled settings sync for {game} with settings file {game.settings_path}.")
        newline()
    print(f"Configured settings sync for {len(games)} games.")

def write_sunshine_config(library: Library):
    path = Path(input(f"Input the path to write the config to (press enter to use the default of {DEFAULT_SUNSHINE_CONFIG_PATH}): ") or DEFAULT_SUNSHINE_CONFIG_PATH).resolve()
    if path.is_file():
        if not yes_or_no(f"Config file {path} already exists. Do you want to overwrite it?"):
            print('Did not write Sunshine config.')
            return
    print('Writing Sunshine config...')
    json_dict = library.to_sunshine_config_json_dict(PRE_LAUNCHER_PATH, LAUNCHER_PATH, TEARDOWN_PATH, SETTINGS_SYNC_PATH, STATIC_ART_DIR, ART_CACHE_DIR)
    with path.open(mode='w', encoding='utf-8') as file:
        json.dump(json_dict, file, ensure_ascii=False, indent=4)
    newline()
    print(f"Saved Sunshine config to {path}. You may need to restart Sunshine for the changes to go into effect.")

def print_menu():
    print('1. List loaded games')
    print('2. Remove game from library')
    print('3. Return removed game to library')
    print('4. Configure non-steam game')
    print('5. Configure game settings synchronization')
    print('6. Write games to Sunshine config')
    print('7. Quit')

if __name__ == '__main__':
    print("Loading cached library...")
    try:
        library = Library.from_file(LIBRARY_CACHE)
    except BaseException as e:
        print(f"Failed to read cached library. It may be corrupted. Quitting to avoid overwriting it. Error was: {traceback.format_exc()}")
        sys.exit(-1)
    print("Syncing library with Steam games...")
    library.sync_library_with_steam()
    library.to_file(LIBRARY_CACHE)
    newline()

    while True:
        newline()
        print_menu()
        choice = int(input('Please select a menu action (number): '))
        if choice == 1:
            library.print()
        elif choice == 2:
            remove_game(library)
        elif choice == 3:
            remove_exclusion(library)
        elif choice == 4:
            configure_non_steam_game(library)
        elif choice == 5:
            configure_game_settings_sync(library)
        elif choice == 6:
            try:
                write_sunshine_config(library)
            except BaseException as e:
                newline()
                print(f"Failed to write Sunshine config. Error was: {traceback.format_exc()}")
        elif choice == 7:
            exit(0)
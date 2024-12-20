import json
import os
import traceback
from typing import List
from util.library import *
from util.steam import *

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
LAUNCHER_PATH = os.path.join(SCRIPT_DIR, 'launcher.py')
TEARDOWN_PATH = os.path.join(SCRIPT_DIR, 'teardown.py')
SETTINGS_SYNC_PATH = os.path.join(SCRIPT_DIR, 'settings-sync.py')
LIBRARY_CACHE = os.path.join(SCRIPT_DIR, ".library-cache")
ART_CACHE_DIR = os.path.join(SCRIPT_DIR, ".converted-artwork-cache")
STATIC_ART_DIR = os.path.join(SCRIPT_DIR, "static-artwork")
DEFAULT_SUNSHINE_CONFIG_PATH = r'C:\Program Files\Sunshine\config\apps.json'
DEFAULT_SHORTCUT_DIR = os.path.join(SCRIPT_DIR, 'shortcuts')

RANGE_DELIMETER_REGEX = re.compile(r'\s*,\s*')
RANGE_REGEX = re.compile(r'^(\d+)\s*\-\s*(\d+)|(\d+)$')

_ORIG_INPUT = input

# We always want to go to a new line before and after receiving input
def input(prompt: str) -> str:
    print('')
    result = _ORIG_INPUT(prompt)
    print('')
    return result

def select_games(initial_prompt: str, confirmation_prompt: str, games: List[Game]) -> List[Game]:
    Library.print_game_list(games)

    game_indices = {}
    raw_input = input(initial_prompt).strip()
    for range_str in RANGE_DELIMETER_REGEX.split(raw_input):
        range_match = RANGE_REGEX.match(range_str)
        if not range_match:
            print(f"Error: Input '{range_str}' is not a valid numeric range")
            print('')
            return []

        if range_match.group(3):
            idx = int(range_match.group(3))
            if idx < 1 or idx > len(games):
                print(f"Error: Game number {idx} does not exist.")
                print('')
                return []

            game_indices[idx] = True
        else:
            lower = int(range_match.group(1))
            upper = int(range_match.group(2))

            if upper < lower:
                print(f"Error: Range '{range_str}' has upper bound greater than lower bound")
                print('')
                return []

            for idx in range(lower, upper + 1):
                if idx < 1 or idx > len(games):
                    print(f"Error: Game number {idx} does not exist.")
                    print('')
                    return []
                game_indices[idx] = True

    selected_games = [games[idx - 1] for idx in sorted(game_indices.keys())]
    print(f"You selected the following {len(selected_games)} games:")
    Library.print_game_list(selected_games)
    choice = ''
    while choice != 'y' and choice != 'n':
        choice = input(f"{confirmation_prompt} (y/n): ")
    if choice == 'n':
        return []
    return selected_games

def add_non_steam_game(library: Library):
    non_steam_games = sorted(get_non_steam_games())
    non_steam_games = library.filter_loaded_non_steam_games(non_steam_games)
    print(f"Found {len(non_steam_games)} non-steam games:")
    games = select_games('Input the number of the game(s) to add: ',
                         "Are you sure you'd like to add the above games?",
                         non_steam_games)
    print(f"Will add {len(games)} non-steam games.")
    for game in games:
        print('')
        print(f"Adding {game}...")
        id = input('Input the steam ID of non-steam game. You can find this by creating a desktop shortcut to the game, then viewing the properties of the shortcut. ID: ')
        game.id = id
        process_name = input(f"Input the process name to track run status (press enter to use the default of {game.process_name}): ")
        if process_name != '':
            game.process_name = process_name
        library.add_game(game)
        library.to_file(LIBRARY_CACHE)
        print(f"Added {game} to library.")

def remove_game(library: Library):
    print(f"There are currently {len(library.get_games())} games in your library:")
    games = select_games('Input the number of the game(s) to remove: ',
                         "Are you sure you'd like to remove the above games?",
                         library.get_games())
    print(f"Will remove {len(games)} games.")
    for game in games:
        library.remove_game(game)
        library.to_file(LIBRARY_CACHE)
        print(f"Removed {game} from library.")

def remove_exclusion(library: Library):
    print(f"There are currently {len(library.get_exclusions())} games previously removed from the library:")
    games = select_games('Input the number of the game(s) to return to your library: ',
                         "Are you sure you'd like to return the above games to your library?",
                         library.get_exclusions())
    print(f"Will return {len(games)} games to your library.")
    for game in games:
        library.remove_exclusion(game)
        library.to_file(LIBRARY_CACHE)
        print(f"Added {game} back to library.")

def config_game_settings_sync(library: Library):
    print(f"There are currently {len(library.get_games())} games in your library:")
    games = select_games('Input the number of the game(s) to configure settings sync for: ',
                         "Are you sure you'd like to configure settings sync for the above games?",
                         library.get_games())
    print(f"Will configure settings sync for {len(games)} games.")
    for game in games:
        print('')
        print(f"Configuring settings sync for {game}...")
        if game.settings_path:
            choice = ''
            while choice != 'y' and choice != 'n':
                choice = input(f"Settings sync already enabled for {game} with settings file {game.settings_path}. Would you like to disable it? (y/n): ")
            if choice == 'y':
                game.settings_path = None
                library.to_file(LIBRARY_CACHE)
                print(f"Disabled settings sync for {game}.")
                continue

        settings_path = input(f"Input the path to the game's settings file{f' ({game.settings_path})' if game.settings_path else ''}: ")
        settings_path = game.settings_path if game.settings_path and settings_path == '' else settings_path
        if not os.path.isfile(settings_path):
            print(f"Error: No file {settings_path} exists.")
            return
        game.settings_path = os.path.abspath(settings_path)
        library.to_file(LIBRARY_CACHE)
        print(f"Enabled settings sync for {game} with settings file {game.settings_path}.")

def write_shortcuts(library: Library):
    dir = input(f"Input the directory to save the shortcuts to (press enter to use the default of {DEFAULT_SHORTCUT_DIR}): ")
    if dir == '':
        dir = DEFAULT_SHORTCUT_DIR
    # Create directory if it doesn't exist
    if not os.path.isdir(dir):
        os.makedirs(dir)
    print('Creating shortcuts...')
    library.write_shortcuts(dir, LAUNCHER_PATH)
    print(f"Created shortcuts in {dir}.")

def write_batch_shortcuts(library: Library):
    dir = input(f"Input the directory to save the batch shortcuts to (press enter to use the default of {DEFAULT_SHORTCUT_DIR}): ")
    if dir == '':
        dir = DEFAULT_SHORTCUT_DIR
    # Create directory if it doesn't exist
    if not os.path.isdir(dir):
        os.makedirs(dir)
    print('Creating batch shortcuts...')
    library.write_batch_shortcuts(dir, LAUNCHER_PATH)
    print(f"Created batch shortcuts in {dir}.")

def write_sunshine_config(library: Library):
    path = input(f"Input the path to write the config to (press enter to use the default of {DEFAULT_SUNSHINE_CONFIG_PATH}): ")
    if path == '':
        path = DEFAULT_SUNSHINE_CONFIG_PATH
    if os.path.isfile(path):
        choice = ''
        while choice != 'y' and choice != 'n':
            choice = input(f"Config file {path} already exists. Do you want to overwrite it? (y/n): ")
        if choice == 'n':
            print('Didn\'t write Sunshine config.')
            return
    print('Writing Sunshine config...')
    json_dict = library.to_sunshine_config_json_dict(LAUNCHER_PATH, TEARDOWN_PATH, SETTINGS_SYNC_PATH, STATIC_ART_DIR, ART_CACHE_DIR)
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(json_dict, file, ensure_ascii=False, indent=4)
    print(f"Saved Sunshine config to {path}. You may need to restart Sunshine for the changes to go into effect.")

def print_menu():
    print('1. List loaded games')
    print('2. Add non-steam game')
    print('3. Remove loaded game from library')
    print('4. Return removed game to library')
    print('5. Configure game settings synchronization')
    print('6. Write games to shortcuts')
    print('7. Write games to batch script shortcuts')
    print('8. Write games to Sunshine config')
    print('9. Quit')

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
    print('Synced library. New non-steam games must be added manually.')

    while True:
        print('')
        print_menu()
        choice = int(input('Please select a menu action (number): '))
        if choice == 1:
            library.print()
        elif choice == 2:
            add_non_steam_game(library)
        elif choice == 3:
            remove_game(library)
        elif choice == 4:
            remove_exclusion(library)
        elif choice == 5:
            config_game_settings_sync(library)
        elif choice == 6:
            try:
                write_shortcuts(library)
            except BaseException as e:
                print('')
                print(f"Failed to write shortcuts. Error was: {traceback.format_exc()}")
        elif choice == 7:
            try:
                write_batch_shortcuts(library)
            except BaseException as e:
                print('')
                print(f"Failed to write batch shortcuts. Error was: {traceback.format_exc()}")
        elif choice == 8:
            try:
                write_sunshine_config(library)
            except BaseException as e:
                print('')
                print(f"Failed to write Sunshine config. Error was: {traceback.format_exc()}")
        elif choice == 9:
            exit(0)
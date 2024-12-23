import json
import traceback
from pathlib import Path
from typing import List
from util.library import *
from util.steam import *

SCRIPT_DIR = Path(__file__).parent
LAUNCHER_PATH = SCRIPT_DIR / 'launcher.py'
TEARDOWN_PATH = SCRIPT_DIR / 'teardown.py'
SETTINGS_SYNC_PATH = SCRIPT_DIR / 'settings-sync.py'
LIBRARY_CACHE = SCRIPT_DIR / ".library-cache"
ART_CACHE_DIR = SCRIPT_DIR / ".converted-artwork-cache"
STATIC_ART_DIR = SCRIPT_DIR / "static-artwork"
DEFAULT_SHORTCUT_DIR = SCRIPT_DIR / 'shortcuts'
DEFAULT_SUNSHINE_CONFIG_PATH = Path(r'C:\Program Files\Sunshine\config\apps.json')

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

def configure_non_steam_game(library: Library):
    print(f"There are currently {len(library.get_non_steam_games())} non-steam games in your library:")
    games = select_games('Input the number of the game(s) to add: ',
                         "Are you sure you'd like to configure the above games?",
                         library.get_non_steam_games())
    print(f"Will configure {len(games)} non-steam games.")
    for game in games:
        print('')
        print(f"Configuring {game}...")
        process_name = input(f"Input the process name to track run status (press enter to keep current value of {game.process_name}): ")
        if process_name != '':
            game.process_name = process_name
        library.to_file(LIBRARY_CACHE)
        print(f"Successfully configured {game}.")

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

def configure_game_settings_sync(library: Library):
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

        settings_path_input = input(f"Input the path to the game's settings file{f' ({game.settings_path})' if game.settings_path else ''}: ")
        settings_path = Path(game.settings_path if game.settings_path and settings_path_input == '' else settings_path_input)
        if not settings_path.is_file():
            print(f"Error: No file {settings_path} exists.")
            return
        game.settings_path = settings_path.resolve()
        library.to_file(LIBRARY_CACHE)
        print(f"Enabled settings sync for {game} with settings file {game.settings_path}.")

def write_shortcuts(library: Library):
    dir = Path(input(f"Input the directory to save the shortcuts to (press enter to use the default of {DEFAULT_SHORTCUT_DIR}): ") or DEFAULT_SHORTCUT_DIR).resolve()
    # Create directory if it doesn't exist
    dir.mkdir(parents=True, exist_ok=True)
    print('Creating shortcuts...')
    library.write_shortcuts(dir, LAUNCHER_PATH)
    print('')
    print(f"Created shortcuts in {dir}.")

def write_batch_shortcuts(library: Library):
    dir = Path(input(f"Input the directory to save the batch shortcuts to (press enter to use the default of {DEFAULT_SHORTCUT_DIR}): ") or DEFAULT_SHORTCUT_DIR).resolve()
    # Create directory if it doesn't exist
    dir.mkdir(parents=True, exist_ok=True)
    print('Creating batch shortcuts...')
    library.write_batch_shortcuts(dir, LAUNCHER_PATH)
    print('')
    print(f"Created batch shortcuts in {dir}.")

def write_sunshine_config(library: Library):
    path = Path(input(f"Input the path to write the config to (press enter to use the default of {DEFAULT_SUNSHINE_CONFIG_PATH}): ") or DEFAULT_SUNSHINE_CONFIG_PATH).resolve()
    if path.is_file():
        choice = ''
        while choice != 'y' and choice != 'n':
            choice = input(f"Config file {path} already exists. Do you want to overwrite it? (y/n): ")
        if choice == 'n':
            print('Did not write Sunshine config.')
            return
    print('Writing Sunshine config...')
    json_dict = library.to_sunshine_config_json_dict(LAUNCHER_PATH, TEARDOWN_PATH, SETTINGS_SYNC_PATH, STATIC_ART_DIR, ART_CACHE_DIR)
    with path.open(mode='w', encoding='utf-8') as file:
        json.dump(json_dict, file, ensure_ascii=False, indent=4)
    print('')
    print(f"Saved Sunshine config to {path}. You may need to restart Sunshine for the changes to go into effect.")

def print_menu():
    print('1. List loaded games')
    print('2. Remove game from library')
    print('3. Return removed game to library')
    print('4. Configure non-steam game')
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
            remove_game(library)
        elif choice == 3:
            remove_exclusion(library)
        elif choice == 4:
            configure_non_steam_game(library)
        elif choice == 5:
            configure_game_settings_sync(library)
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
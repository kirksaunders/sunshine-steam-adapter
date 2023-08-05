import json
import os
from util.library import *
from util.steam import *

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
LAUNCHER_PATH = os.path.join(SCRIPT_DIR, 'launcher.py')
TEARDOWN_PATH = os.path.join(SCRIPT_DIR, 'teardown.py')
LIBRARY_CACHE = os.path.join(SCRIPT_DIR, ".library-cache")
ART_CACHE_DIR = os.path.join(SCRIPT_DIR, ".converted-artwork-cache")
STATIC_ART_DIR = os.path.join(SCRIPT_DIR, "static-artwork")
DEFAULT_SUNSHINE_CONFIG_PATH = r'C:\Program Files\Sunshine\config\apps.json'
DEFAULT_SHORTCUT_DIR = os.path.join(SCRIPT_DIR, 'shortcuts')

def add_non_steam_game(library: Library):
    non_steam_games = sorted(get_non_steam_games())
    non_steam_games = library.filter_loaded_non_steam_games(non_steam_games)
    print(f"Found {len(non_steam_games)} non-steam games:")
    Library.print_game_list(non_steam_games)
    print('')
    choice = int(input('Input the number of the game to add: '))
    print('')
    if choice < 1 or choice > len(non_steam_games):
        print(f"Error: Game number {choice} does not exist.")
    else:
        game = non_steam_games[choice - 1]
        id = input("Input the steam ID of non-steam game. You can find this by creating a desktop shortcut to the game, then viewing the properties of the shortcut. ID: ")
        print('')
        game.id = id
        process_name = input(f"Input the process name to track run status (press enter to use the default of {game.process_name}): ")
        print('')
        if process_name != '':
            game.process_name = process_name
        library.add_game(game)
        library.to_file(LIBRARY_CACHE)
        print(f"Added {game} to library.")

def remove_game(library: Library):
    library.print()
    print('')
    choice = int(input("Input the number of the game to remove: "))
    print('')
    if choice < 1 or choice > len(library.get_games()):
        print(f"Error: Game number {choice} does not exist.")
    else:
        game = library.remove_game(choice - 1)
        library.to_file(LIBRARY_CACHE)
        print(f"Removed {game} from library.")

def remove_exclusion(library: Library):
    print(f"There are {len(library.get_exclusions())} games removed from the list:")
    library.print_exclusions()
    print('')
    choice = int(input("Input the number of the game to add back to library: "))
    print('')
    if choice < 1 or choice > len(library.get_exclusions()):
        print(f"Error: Game number {choice} does not exist in exclusions.")
    else:
        game = library.remove_exclusion(choice - 1)
        library.to_file(LIBRARY_CACHE)
        print(f"Added {game} back to library.")

def write_shortcuts(library: Library):
    dir = input(f"Input the directory to save the shortcuts to (press enter to use the default of {DEFAULT_SHORTCUT_DIR}): ")
    if dir == '':
        dir = DEFAULT_SHORTCUT_DIR
    print('')
    # Create directory if it doesn't exist
    if not os.path.exists(dir):
        os.makedirs(dir)
    print('Creating shortcuts...')
    library.write_shortcuts(dir, LAUNCHER_PATH)
    print(f"Created shortcuts in {dir}.")

def write_batch_shortcuts(library: Library):
    dir = input(f"Input the directory to save the batch shortcuts to (press enter to use the default of {DEFAULT_SHORTCUT_DIR}): ")
    if dir == '':
        dir = DEFAULT_SHORTCUT_DIR
    print('')
    # Create directory if it doesn't exist
    if not os.path.exists(dir):
        os.makedirs(dir)
    print('Creating batch shortcuts...')
    library.write_batch_shortcuts(dir, LAUNCHER_PATH)
    print(f"Created batch shortcuts in {dir}.")

def write_sunshine_config(library: Library):
    path = input(f"Input the path to write the config to (press enter to use the default of {DEFAULT_SUNSHINE_CONFIG_PATH}): ")
    if path == '':
        path = DEFAULT_SUNSHINE_CONFIG_PATH
    print('')
    if os.path.isfile(path):
        choice = ''
        while choice != 'y' and choice != 'n':
            choice = input(f"Config file {path} already exists. Do you want to overwrite it? (y/n): ")
        print('')
        if choice == 'n':
            print('Didn\'t write Sunshine config.')
            return
    print('Writing Sunshine config...')
    json_dict = library.to_sunshine_config_json_dict(LAUNCHER_PATH, TEARDOWN_PATH, STATIC_ART_DIR, ART_CACHE_DIR)
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(json_dict, file, ensure_ascii=False, indent=4)
    print(f"Saved Sunshine config to {path}. You may need to restart Sunshine for the changes to go into effect.")

def print_menu():
    print('1. List loaded games')
    print('2. Add non-steam game')
    print('3. Remove loaded game from library')
    print('4. Return removed game to library')
    print('5. Write games to shortcuts')
    print('6. Write games to batch script shortcuts')
    print('7. Write games to Sunshine config')
    print('8. Quit')

if __name__ == '__main__':
    print("Loading cached library...")
    library = Library.from_file(LIBRARY_CACHE)
    print("Loading official steam games...")
    library.load_steam_games()
    print("Updating non-steam games...")
    library.update_non_steam_games()
    library.to_file(LIBRARY_CACHE)
    print('Loaded all games. New non-steam games must be added manually.')

    while True:
        print('')
        print_menu()
        print('')
        choice = int(input('Please select a menu action (number): '))
        print('')
        if choice == 1:
            library.print()
        elif choice == 2:
            add_non_steam_game(library)
        elif choice == 3:
            remove_game(library)
        elif choice == 4:
            remove_exclusion(library)
        elif choice == 5:
            write_shortcuts(library)
        elif choice == 6:
            write_batch_shortcuts(library)
        elif choice == 7:
            write_sunshine_config(library)
        elif choice == 8:
            exit(0)
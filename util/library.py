import json
import sys
from typing import List
from typing import Optional, Self
import win32com.client
from util.art import *
from util.game import *
from util.steam import *
    
class Library:
    def __init__(self, non_steam_games: Optional[List[Game]] = None, exclusions: Optional[List[Game]] = None):
        self.games = [] if non_steam_games is None else non_steam_games
        self.exclusions = [] if exclusions is None else exclusions

        self._sort_games()
        self._sort_exclusions()

    def get_games(self) -> List[Game]:
        return self.games
    
    def get_exclusions(self) -> List[Game]:
        return self.exclusions
        
    def get_steam_games(self) -> List[Game]:
        return [game for game in self.games if not game.is_non_steam()]

    def get_non_steam_games(self) -> List[Game]:
        return [game for game in self.games if game.is_non_steam()]
    
    def filter_loaded_non_steam_games(self, non_steam_games: List[Game]) -> List[Game]:
        return [game for game in non_steam_games if not game in self.games]

    def add_game(self, game: Game):
        self.games.append(game)
        self._sort_games()

    def add_exclusion(self, exclusion: Game):
        self.exclusions.append(exclusion)
        self._sort_exclusions()

    def remove_game(self, index: int) -> Game:
        game = self.games.pop(index)
        if not game.is_non_steam():
            self.add_exclusion(game)
        return game
    
    def remove_exclusion(self, index: int) -> Game:
        game = self.exclusions.pop(index)
        self.add_game(game)
        return game
    
    def print(self):
        Library.print_game_list(self.games)

    def print_exclusions(self):
        Library.print_game_list(self.exclusions)

    @staticmethod
    def print_game_list(game_list: List[Game]):
        for index, game in enumerate(game_list):
            print(f"{index + 1}.\t{game}")

    def load_steam_games(self):
        steam_games = get_installed_steam_games(self.exclusions)
        count = 0
        for game in steam_games:
            if not game in self.games:
                self.games.append(game)
                count += 1
        self._sort_games()
        print(f"Loaded {count} official steam games.")

    def update_non_steam_games(self):
        update_count = 0
        remove_count = 0
        index = 0
        while index < len(self.games):
            game = self.games[index]
            found = False
            for non_steam_game in get_non_steam_games():
                if game.alt_id == non_steam_game.alt_id:
                    if game.name != non_steam_game.name:
                        print(f"Updating {game} name to match newly read value: {non_steam_game.name}")
                        game.name = non_steam_game.name
                        update_count += 1
                    found = True
            if game.is_non_steam() and not found:
                print('')
                choice = ''
                while choice != 'y' and choice != 'n':
                    choice = input(f"Library cache contains non-steam game {game}. But couldn't find non-steam game in steam library. Do you want to remove it? (y/n): ")
                print('')
                if choice == 'y':
                    self.remove_game(index)
                    remove_count += 1
                    index -= 1
                    print('Removed non-steam game {game} from library.')
                else:
                    print('Didn\'t remove game.')
            index += 1

        print(f"Updated {update_count} and removed {remove_count} non-steam games.")
    
    def to_file(self, file_path: str):
        with open(file_path, mode='w') as file:
            json.dump(self.to_json_dict(), file, ensure_ascii=False, indent=4)

    @classmethod
    def from_file(cls, file_path: str) -> Self:
        if not os.path.isfile(file_path):
            return cls()
        with open(file_path, mode='r') as file:
            return cls.from_json_dict(json.load(file))

    def to_json_dict(self) -> dict:
        return {
            'non_steam_games': [game.to_json_dict() for game in self.get_non_steam_games()],
            'exclusions': [game.to_json_dict() for game in self.exclusions]
        }
    
    @classmethod
    def from_json_dict(cls, j: dict) -> Self:
        non_steam_games = [Game.from_json_dict(game) for game in j['non_steam_games']]
        exclusions = [Game.from_json_dict(game) for game in j['exclusions']]
        library = cls(non_steam_games=non_steam_games, exclusions=exclusions)
        return library
    
    def to_sunshine_config_json_dict(self, launcher_path: str, teardown_path: str, static_art_dir: str, art_cache_dir: str) -> dict:
        pythonw_path = os.path.join(os.path.abspath(os.path.dirname(sys.executable)), 'pythonw.exe')
        config: dict = {
            'env': {
                'PATH': "$(PATH);$(ProgramFiles(x86))\\Steam"
            },
        }
        apps = [
            {
                'name': 'Desktop',
                'image-path': 'desktop.png'
            },
            {
                'name': 'Steam Big Picture',
                'cmd': f"{pythonw_path} {launcher_path}",
                'prep-cmd': [
                    {
                        'do': '',
                        'undo': f"{pythonw_path} {teardown_path} detached",
                        'elevated': 'true'
                    }
                ],
                'image-path': os.path.join(static_art_dir, 'steam-big-picture.png')
            },
        ]
        config['apps'] = apps

        for game in self.games:
            apps.append({
                'name': game.name,
                'cmd': f"{pythonw_path} {launcher_path} {game.launcher_args()}",
                'prep-cmd': [
                    {
                        'do': '',
                        'undo': f"{pythonw_path} {teardown_path} detached",
                        'elevated': 'true'
                    }
                ],
                'image-path': game.get_cover_art_path(STEAM_CONFIG_PATH, art_cache_dir),
            })
        return config

    def write_shortcuts(self, shortcut_dir: str, launcher_path: str):
        for game in self.games:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(os.path.join(shortcut_dir, f"{game.sanitized_name()}.lnk"))
            shortcut.Targetpath = str(launcher_path)
            shortcut.Arguments = game.launcher_args()
            # TODO: Write icons
            # shortcut.IconLocation = icon
            shortcut.WindowStyle = 1 # 7 - Minimized, 3 - Maximized, 1 - Normal
            shortcut.save()

    def write_batch_shortcuts(self, shortcut_dir: str, launcher_path: str):
        for game in self.games:
            with open(os.path.join(shortcut_dir, f"{game.sanitized_name()}.bat"), 'w') as file:
                file.write(f"\"{launcher_path}\" {game.launcher_args()}\n")

    def _sort_games(self):
        self.games = sorted(self.games)

    def _sort_exclusions(self):
        self.exclusions = sorted(self.exclusions)

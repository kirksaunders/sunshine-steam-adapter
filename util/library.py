import json
import sys
import win32com.client
from typing import List
from typing import Optional, Self
from util.art import *
from util.game import *
from util.steam import *

class Library:
    def __init__(self, games: Optional[List[Game]] = None, exclusions: Optional[List[Game]] = None):
        self.games = [] if games is None else games
        self.exclusions = [] if exclusions is None else exclusions

        self._sort_games()
        self._sort_exclusions()

    def get_game(self, index: int) -> Game:
        return self.games[index]

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

    def remove_game(self, game: Game, skip_exclusion: bool = False):
        self.games.remove(game)
        if not skip_exclusion:
            self.add_exclusion(game)

    def remove_exclusion(self, game: Game):
        self.exclusions.remove(game)
        self.add_game(game)

    def purge_exclusion(self, game: Game):
        self.exclusions.remove(game)

    def print(self):
        Library.print_game_list(self.games)

    def print_exclusions(self):
        Library.print_game_list(self.exclusions)

    @staticmethod
    def print_game_list(game_list: List[Game]):
        for index, game in enumerate(game_list):
            print(f"{index + 1}.\t{game}")

    def sync_library_with_steam(self):
        update_count = 0
        remove_count = 0
        add_count = 0
        purge_count = 0
        new_games = get_installed_steam_games() + get_non_steam_games()

        # Add/update existing games if names have changed
        for new_game in new_games:
            found = False
            for game in self.games:
                if game == new_game:
                    if game.name != new_game.name:
                        print(f"Updating {game} name to match newly read value: {new_game.name}")
                        game.name = new_game.name
                        update_count += 1
                    found = True
                    break

            if not found:
                if new_game in self.exclusions:
                    print(f"Not adding {new_game} to library, since it was previously removed.")
                else:
                    self.add_game(new_game)
                    add_count += 1
                    print(f"Added {new_game} to library.")

        # Remove games from library if they weren't found in Steam
        for game in self.games:
            if not game in new_games:
                print('')
                choice = ''
                while choice != 'y' and choice != 'n':
                    choice = input(f"Library contains {game}, but couldn't find it in Steam library. Do you want to remove it? (y/n): ")
                print('')
                if choice == 'y':
                    self.remove_game(game, skip_exclusion=True)
                    remove_count += 1
                    print(f"Removed game {game} from library.")
                else:
                    print(f"Did not remove game {game}.")

        # Remove exclusions if they weren't found in Steam. One downside: if user excludes a game, then
        # uninstalls it, then runs the script, it will be removed from the exclusions. If user then
        # reinstalls it and expects it to be excluded still, that won't happen. This seems like a fine
        # tradeoff to prevent stale entries in the exclusion list.
        for game in self.exclusions:
            if not game in new_games:
                print('')
                choice = ''
                while choice != 'y' and choice != 'n':
                    choice = input(f"Library contains exclusion for {game}, but couldn't find it in Steam library. Do you want to remove it? (y/n): ")
                print('')
                if choice == 'y':
                    self.purge_exclusion(game)
                    purge_count += 1
                    print(f"Purged game {game} from exclusions.")
                else:
                    print(f"Did not purge game {game} from exclusions.")

        self._sort_games()
        print('')
        print(f"Added {add_count} games, updated {update_count} games, removed {remove_count} games, and purged {purge_count} exclusions based on Steam library.")

    def to_file(self, file_path: str):
        with open(file_path, mode='w', encoding='utf8') as file:
            json.dump(self.to_json_dict(), file, ensure_ascii=False, indent=4)

    @classmethod
    def from_file(cls, file_path: str) -> Self:
        if not os.path.isfile(file_path):
            return cls()
        with open(file_path, mode='r', encoding='utf8') as file:
            return cls.from_json_dict(json.load(file))

    def to_json_dict(self) -> dict:
        return {
            'games': [game.to_json_dict() for game in self.games],
            'exclusions': [game.to_json_dict() for game in self.exclusions]
        }

    @classmethod
    def from_json_dict(cls, j: dict) -> Self:
        # Support legacy format, which only saved non-steam games
        games_arr = j.get('non_steam_games') or j['games']
        games = [Game.from_json_dict(game) for game in games_arr]
        exclusions = [Game.from_json_dict(game) for game in j['exclusions']]
        library = cls(games=games, exclusions=exclusions)
        return library

    def to_sunshine_config_json_dict(self, launcher_path: str, teardown_path: str, settings_sync_path: str, static_art_dir: str, art_cache_dir: str) -> dict:
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
                        'elevated': 'false'
                    }
                ],
                'image-path': os.path.join(static_art_dir, 'steam-big-picture.png')
            },
        ]
        config['apps'] = apps

        for game in self.games:
            prep_cmds = [
                {
                    'do': '',
                    'undo': f"{pythonw_path} {teardown_path} detached",
                    'elevated': 'false'
                }
            ]
            if game.settings_path:
                prep_cmds.insert(0, {
                    'do': f"{pythonw_path} {settings_sync_path} {game.settings_sync_args()} load",
                    'undo': f"{pythonw_path} {settings_sync_path} {game.settings_sync_args()} save",
                    'elevated': 'false'
                })

            apps.append({
                'name': game.name,
                'cmd': f"{pythonw_path} {launcher_path} {game.launcher_args()}",
                'prep-cmd': prep_cmds,
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

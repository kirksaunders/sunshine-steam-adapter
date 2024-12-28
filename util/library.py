import json
import sys
import win32com.client
from typing import List
from typing import Optional, Self
from util.art import *
from util.game import *
from util.io import *
from util.steam import *

class Library:
    __RANGE_DELIMETER_REGEX = re.compile(r'\s*,\s*')
    __RANGE_REGEX = re.compile(r'^(\d+)\s*\-\s*(\d+)|(\d+)$')

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
    def print_game_list(games: List[Game]):
        for index, game in enumerate(games):
            print(f"{index + 1}.\t{game}")

    @staticmethod
    def select_games(initial_prompt: str, confirmation_prompt: str, games: List[Game]) -> List[Game]:
        Library.print_game_list(games)

        game_indices = {}
        raw_input = input(initial_prompt).strip()
        for range_str in Library.__RANGE_DELIMETER_REGEX.split(raw_input):
            range_match = Library.__RANGE_REGEX.match(range_str)
            if not range_match:
                print(f"Error: Input '{range_str}' is not a valid numeric range")
                newline()
                return []

            if range_match.group(3):
                idx = int(range_match.group(3))
                if idx < 1 or idx > len(games):
                    print(f"Error: Game number {idx} does not exist.")
                    newline()
                    return []

                game_indices[idx] = True
            else:
                lower = int(range_match.group(1))
                upper = int(range_match.group(2))

                if upper < lower:
                    print(f"Error: Range '{range_str}' has upper bound greater than lower bound")
                    newline()
                    return []

                for idx in range(lower, upper + 1):
                    if idx < 1 or idx > len(games):
                        print(f"Error: Game number {idx} does not exist.")
                        newline()
                        return []
                    game_indices[idx] = True

        selected_games = [games[idx - 1] for idx in sorted(game_indices.keys())]
        print(f"You selected the following {len(selected_games)} games:")
        Library.print_game_list(selected_games)
        if not yes_or_no(confirmation_prompt):
            return []
        return selected_games

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
                if yes_or_no(f"Library contains {game}, but couldn't find it in Steam library. Do you want to remove it?"):
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
                if  yes_or_no(f"Library contains exclusion for {game}, but couldn't find it in Steam library. Do you want to remove it?"):
                    self.purge_exclusion(game)
                    purge_count += 1
                    print(f"Purged game {game} from exclusions.")
                else:
                    print(f"Did not purge game {game} from exclusions.")

        self._sort_games()
        newline()
        print(f"Added {add_count} games, updated {update_count} games, removed {remove_count} games, and purged {purge_count} exclusions based on Steam library.")

    def to_file(self, file_path: Path):
        with file_path.open(mode='w', encoding='utf8') as file:
            json.dump(self.to_json_dict(), file, ensure_ascii=False, indent=4)

    @classmethod
    def from_file(cls, file_path: Path) -> Self:
        if not file_path.is_file():
            return cls()
        with file_path.open(mode='r', encoding='utf8') as file:
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

    def to_sunshine_config_json_dict(self, pre_launcher_path: Path, launcher_path: Path, teardown_path: Path, settings_sync_path: Path, static_art_dir: Path, art_cache_dir: Path) -> dict:
        pythonw_path = Path(sys.executable).parent.resolve() / 'pythonw.exe'
        config: dict = {
            'env': {
                'PATH': "$(PATH);$(ProgramFiles(x86))\\Steam"
            },
        }
        common_options: dict = {
            'auto-detach': 'false'
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
                        'do': f"{pythonw_path} {pre_launcher_path}",
                        'undo': f"{pythonw_path} {teardown_path} detached",
                        'elevated': 'false'
                    }
                ],
                'image-path': str(static_art_dir / 'steam-big-picture.png'),
                **common_options
            },
        ]
        config['apps'] = apps

        for game in self.games:
            prep_cmds = [
                {
                    'do': f"{pythonw_path} {pre_launcher_path}",
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
                'image-path': str(game.get_cover_art_path(STEAM_CONFIG_PATH, art_cache_dir) or ''),
                **common_options
            })
        return config

    def _sort_games(self):
        self.games = sorted(self.games)

    def _sort_exclusions(self):
        self.exclusions = sorted(self.exclusions)

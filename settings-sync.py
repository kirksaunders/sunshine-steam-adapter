import argparse
import os
import shutil
from util.log import *

SCRIPT_DIR = Path(__file__).parent
SETTINGS_CACHE = SCRIPT_DIR / ".settings-cache"
LOG = Logger(SCRIPT_DIR / 'logs' / 'settings-sync-log.txt')

def backup_settings(settings_path: Path):
    backup_path = settings_path.with_suffix(settings_path.suffix + '.bak')
    LOG.log(f"Backing up game's settings file to {backup_path}")
    shutil.copy2(settings_path, backup_path)
    if not backup_path.is_file():
        raise RuntimeError('Could not find settings backup after doing copy')
    LOG.log('Successfully backed up game\'s settings file')

def restore_backup_settings(settings_path: Path):
    backup_path = settings_path.with_suffix(settings_path.suffix + '.bak')
    LOG.log(f"Restoring game's backup settings file at {backup_path}")
    if not backup_path.is_file():
        LOG.log("No settings backup file found. Nothing to do")
        return
    shutil.copy2(backup_path, settings_path)
    LOG.log('Successfully restored game\'s backup settings file')

def delete_backup_settings(settings_path: Path):
    backup_path = settings_path.with_suffix(settings_path.suffix + '.bak')
    LOG.log(f"Deleting game's backup settings file at {backup_path}.")
    if not backup_path.is_file():
        LOG.log("No settings backup file found. Nothing to do")
        return
    backup_path.unlink()
    LOG.log('Successfully deleted game\'s backup settings file')

def get_save_path(game_id: str, client_id: str, settings_path: Path) -> Path:
    return SETTINGS_CACHE / game_id / client_id / settings_path.name

def save_settings(game_id: str, client_id: str, settings_path: Path):
    save_path = get_save_path(game_id, client_id, settings_path)
    LOG.log(f"Saving game's settings file to {save_path}")
    save_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(settings_path, save_path)
    LOG.log("Saved settings for game")

def load_settings(game_id: str, client_id: str, settings_path: Path):
    save_path = get_save_path(game_id, client_id, settings_path)
    LOG.log(f"Loading game's settings file from {save_path}")
    if not save_path.is_file():
        LOG.log("No saved settings file found. Nothing to do")
        return
    shutil.copy2(save_path, settings_path)
    LOG.log("Loaded settings to game")

def get_client_id_from_env() -> str:
    width = os.environ["SUNSHINE_CLIENT_WIDTH"]
    height = os.environ["SUNSHINE_CLIENT_HEIGHT"]
    fps = os.environ["SUNSHINE_CLIENT_FPS"]
    return f"{width}x{height}x{fps}"

def load_handler(args):
    client_id = get_client_id_from_env()
    LOG.log(f"Running settings sync loader with game id={args.game_id}, client id={client_id}, and settings path={args.settings_path}")
    backup_settings(args.settings_path)
    load_settings(args.game_id, client_id, args.settings_path)

def save_handler(args):
    client_id = get_client_id_from_env()
    LOG.log(f"Running settings sync saver with game id={args.game_id}, client id={client_id}, and settings path={args.settings_path}")
    save_settings(args.game_id, client_id, args.settings_path)
    restore_backup_settings(args.settings_path)
    delete_backup_settings(args.settings_path)

def main():
    parser = argparse.ArgumentParser(
        prog='Sunshine Game Settings Syncer',
        description='This is a tool used to synchronize game settings based on client resolution. Any changes made during a stream are restored the next time you stream.'
    )
    parser.add_argument('-g', '--game_id', type=str, required=True, help='The game id to sync settings for.')
    parser.add_argument('-s', '--settings_path', type=Path, required=True, help='The path to the game\'s settings file.')
    subparsers = parser.add_subparsers(required=True, help='What action to take.')

    load_parser = subparsers.add_parser('load', help='Load the saved settings file for the client.')
    load_parser.set_defaults(handler=load_handler)

    save_parser = subparsers.add_parser('save', help='Save the current settings file for the client.')
    save_parser.set_defaults(handler=save_handler)

    args = parser.parse_args()
    args.handler(args)

if __name__ == '__main__':
    LOG.with_error_catching(main, 'settings sync script')

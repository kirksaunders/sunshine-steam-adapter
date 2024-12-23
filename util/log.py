import traceback
from datetime import datetime
from pathlib import Path

class Logger:
    def __init__(self, log_file_path: Path):
        dir_path = log_file_path.parent
        dir_path.mkdir(parents=True, exist_ok=True)
        self.file = log_file_path.open(mode='a')

    def log(self, *args):
        print(f"{datetime.now()}:", *args, file=self.file)

    def with_error_catching(self, func, name: str):
        try:
            self.log('=' * 100)
            self.log(f"Started running {name}")
            func()
        except BaseException as e:
            self.log(f"Script failed with exception: {traceback.format_exc()}")
            raise e
        finally:
            self.log(f"Finished running {name}")
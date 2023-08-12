import os
import traceback
from datetime import datetime

class Logger:
    def __init__(self, log_file_path: str):
        dir_path = os.path.dirname(log_file_path)
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)

        self.file = open(log_file_path, 'a')

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
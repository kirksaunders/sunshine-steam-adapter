import glob
import re
from util.art import *

class Game:
    def __init__(self, id, name, alt_id=None, process_name=None):
        self.id = id
        self.name = name
        if alt_id:
            assert not process_name is None
        if process_name:
            assert not alt_id is None
        self.alt_id = alt_id
        self.process_name = process_name

    def __str__(self):
        suffix = f", Process name = {self.process_name}) *Non-Steam" if self.process_name else ')'
        return f"{self.name} (ID={self.id}{suffix}"
    
    def __lt__(self, other):
        return self.name < other.name
    
    def __eq__(self, other):
        return self.id == other.id or (self.alt_id != None and self.alt_id == other.alt_id)
    
    def is_non_steam(self):
        return not self.alt_id is None
    
    def sanitized_name(self):
        return re.sub(r'[^\w_. -]', '_', self.name)
    
    def launcher_args(self):
        args = [f"-g={self.id}"]
        if self.process_name:
            args.append(f"-p={self.process_name}")
        return ' '.join(args)
    
    def serialize(self):
        if self.alt_id:
            return f"{self.id}|{self.name}|{self.alt_id}|{self.process_name}"
        else:
            return f"{self.id}|{self.name}"
    
    def deserialize(string):
        elements = string.strip().split('|')
        assert len(elements) == 2 or len(elements) == 4
        return Game(*elements)
    
    def to_json_dict(self):
        j = {
            'id': self.id,
            'name': self.name
        }
        if self.alt_id:
            j['alt_id'] = self.alt_id
        if self.process_name:
            j['process_name'] = self.process_name
        return j
    
    def from_json_dict(j):
        return Game(id=j.get('id'), name=j.get('name'), alt_id=j.get('alt_id'), process_name=j.get('process_name'))
    
    def get_cover_art_path(self, steam_config_path, art_cache_dir_path):
        app_id = self.alt_id or self.id

        # First look in grid (custom artwork)
        matches = glob.glob(os.path.join(steam_config_path, f"grid/{app_id}p.*"))
        if len(matches) > 0:
            assert len(matches) == 1
            match = matches[0]
            if os.path.splitext(match)[1] == '.png':
                return match
            else:
                return convert_to_png(match, art_cache_dir_path)
        
        # Then look in librarycache
        matches = glob.glob(os.path.abspath(os.path.join(steam_config_path, f"../../../appcache/librarycache/{app_id}_library_600x900.*")))
        if len(matches) > 0:
            assert len(matches) == 1
            match = matches[0]
            if os.path.splitext(match)[1] == '.png':
                return match
            else:
                return convert_to_png(match, art_cache_dir_path)
        
        # Just return empty string if we can't find anything
        return ''
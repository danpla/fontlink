
import json
from . import conf


class Settings(dict):

    def load(self):
        try:
            with open(conf.CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.update(json.load(f))
        except OSError:
            pass

    def save(self):
        try:
            with open(conf.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self, f, ensure_ascii=False, indent=2, sort_keys=True)
        except OSError:
            pass

settings = Settings()

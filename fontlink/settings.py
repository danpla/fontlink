
import json
import os

from . import config


class _Settings(dict):

    _FILE = os.path.join(config.CONFIG_DIR, 'settings.json')

    def load(self):
        try:
            with open(self._FILE, 'r', encoding='utf-8') as f:
                self.update(json.load(f))
        except (ValueError, OSError):
            pass

    def save(self):
        try:
            with open(self._FILE, 'w', encoding='utf-8') as f:
                json.dump(
                    self, f, ensure_ascii=False, indent=2, sort_keys=True)
        except OSError:
            pass


settings = _Settings()

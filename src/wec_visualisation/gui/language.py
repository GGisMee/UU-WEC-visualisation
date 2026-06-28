import tomllib
import os
import sys

class LanguageManager:
    def __init__(self, default_lang="english"):
        self.lang_dir = self.get_asset_path(os.path.join("assets", "lang"))
        self.strings = {}
        self.load_language(default_lang)

    def get_asset_path(self, relative_path):
        base_path = getattr(sys, '_MEIPASS', None)
        if base_path is None:
            # language.py is in src/winding/gui/, so parent of parent is src/winding/
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)

    def load_language(self, lang_name):
        file_path = os.path.join(self.lang_dir, f"{lang_name}.toml")
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                self.strings = tomllib.load(f)
        else:
            print(f"Warning: Language file {file_path} not found!")
            self.strings = {}

    def get(self, dotted_key, default=None):
        """Retrieves a nested string or list from the TOML data using dotted notation."""
        parts = dotted_key.split(".")
        val = self.strings
        for part in parts:
            if isinstance(val, dict) and part in val:
                val = val[part]
            else:
                return default if default is not None else f"[{dotted_key}]"
        return val

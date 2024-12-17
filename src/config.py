from typing import Union, Dict, Any

import os
from dotenv import load_dotenv

from aqt import mw
from .constants import ConfigKeys


class AnkiConfig:
    def __init__(self):
        self._load_env()
        self.restore_defaults()

    def _load_env(self):
        addon_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(addon_dir, ".env")
        load_dotenv(env_path)

    def set_note_type_config(self, note_type: str, note_type_config: Dict[str, Any]):
        # config.json holds default config options, users modifications
        # are saved to meta.json.
        conf = mw.addonManager.getConfig(__name__)
        if conf is None:
            conf = {}
        conf[note_type] = note_type_config

        print(f"saving {conf} to {__name__}")
        mw.addonManager.writeConfig(__name__, conf)

    def get_note_type_config(self, note_type):
        conf = mw.addonManager.getConfig(__name__)
        return conf.get(note_type, {}) if conf else {}

    def __getattr__(self, item):
        if item in ConfigKeys.allowed_keys:
            conf = mw.addonManager.getConfig(__name__)
            if conf is None:
                raise RuntimeError(f"Unable to retrieve {item} option!")
            return conf[item]
        else:
            raise AttributeError(f"{item} is not a valid attribute!")

    def __setattr__(self, key, value):
        if key in ConfigKeys.allowed_keys:
            conf = mw.addonManager.getConfig(__name__)
            if conf is None:
                raise RuntimeError(f"Unable to set {key} option!")
            conf[key] = value
        else:
            raise AttributeError(f"{key} is not a valid attribute!")

    def restore_defaults(self) -> None:
        defaults = self.get_defaults()
        if not defaults:
            return

        mw.addonManager.writeConfig(__name__, defaults)

    def get_defaults(self) -> Union[Dict[str, Any], None]:
        if not mw:
            return {}

        defaults = mw.addonManager.addonConfigDefaults("reibun_koubou")
        return defaults

    @property
    def claude_api_key(self) -> str:
        """Get Claude API key from environment variables"""
        api_key = os.getenv("CLAUDE_API_KEY")
        if not api_key:
            raise ValueError("CLAUDE_API_KEY not found in environment variables")
        return api_key

    @property
    def debug_mode(self) -> bool:
        return os.getenv("DEBUG_MODE", "false").lower() == "true"

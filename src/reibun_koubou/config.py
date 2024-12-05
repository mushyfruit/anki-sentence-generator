import os
from dotenv import load_dotenv


class Config:
    def __init__(self):
        self.addon_dir = os.path.dirname(os.path.abspath(__file__))
        self._load_env()

    def _load_env(self):
        env_path = os.path.join(self.addon_dir, ".env")
        load_dotenv(env_path)

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

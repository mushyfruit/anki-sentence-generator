import os
import glob
import yaml
import logging

from jinja2 import Environment, FileSystemLoader

from ..config import AnkiConfig

from aqt.utils import showWarning

log = logging.getLogger(__name__)


class PromptManager:
    """Manages templated prompts for generating example sentences.

    Handles loading and rendering of yaml prompt templates with additional
    configurable config prompt options.
    """

    def __init__(self, config: AnkiConfig):
        self.config = config
        self.template_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "templates"
        )
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.templates = self._load_templates()

    def build_reibun_prompt(self, word: str, difficulty: str, context: str) -> str:
        base_prompt = self._get_base_prompt()
        if "{{word}}" not in base_prompt:
            showWarning("Custom prompt must include {{word}} placeholder")
            raise ValueError("Custom prompt must include {{word}} placeholder")

        try:
            return self._render_prompt(base_prompt, word, difficulty, context)
        except Exception as e:
            log.error(f"Failed to generate reibun prompt: {e}")
            raise RuntimeError(f"Failed to generate reibun prompt: {e}") from e

    def _render_prompt(self, base_prompt, word, difficulty, context) -> str:
        required_suffix = self._get_required_prompt()
        full_prompt = self.env.from_string(
            f"{base_prompt}\n\n{required_suffix}"
        ).render(
            word=word,
            difficulty=self._format_difficulty(difficulty),
            context_type=self._format_context(context),
        )
        return full_prompt

    def _format_difficulty(self, difficulty):
        if difficulty is None:
            return None

        return f"Target a JLPT {difficulty} difficulty for the example sentence."

    def _format_context(self, context_type):
        if context_type is None:
            return None

        return f"Ensure the example sentence is suitable for a {context_type} context."

    def _load_templates(self):
        templates = {}

        yaml_pattern = os.path.join(self.template_dir, "*.yaml")
        for yaml_file in glob.glob(yaml_pattern):
            with open(yaml_file, "r", encoding="utf-8") as f:
                yaml_name = os.path.splitext(os.path.basename(yaml_file))[0]
                templates[yaml_name] = yaml.safe_load(f)
        return templates

    def _get_required_prompt(self):
        return self.templates["reibun"]["templates"]["required"]["format"]

    def _get_base_prompt(self):
        # TODO read config
        return self.templates["reibun"]["templates"]["customizable"]["default"]

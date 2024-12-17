import os
import glob
import yaml

from jinja2 import Environment, FileSystemLoader

from ..config import AnkiConfig

from aqt.utils import showWarning


class PromptManager:
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

    def build_reibun_prompt(self, word, difficulty, context):
        base_prompt = self._get_base_prompt()
        required_suffix = self._get_required_prompt()

        if "{{word}}" not in base_prompt:
            showWarning("Custom prompt must include {{word}} placeholder")
            return

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

        return f"Target a {difficulty} difficulty"

    def _format_context(self, context_type):
        if context_type is None:
            return None

        return f"{context_type} context"

    def _load_templates(self):
        templates = {}

        yaml_pattern = os.path.join(self.template_dir, "*.yaml")
        for yaml_file in glob.glob(yaml_pattern):
            with open(yaml_file) as f:
                yaml_name = os.path.splitext(os.path.basename(yaml_file))[0]
                templates[yaml_name] = yaml.safe_load(f)
        return templates

    def _get_required_prompt(self):
        return self.templates["reibun"]["templates"]["required"]["format"]

    def _get_base_prompt(self):
        # TODO read config
        return self.templates["reibun"]["templates"]["customizable"]["default"]

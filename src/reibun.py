from typing import Dict

import json
import logging
from textwrap import dedent

from src.dev.estimate import TokenCostEstimator

from anthropic import Anthropic

from .prompts.manager import PromptManager
from .constants import NoteConfig


MODEL = "claude-3-haiku-20240307"

log = logging.getLogger(__name__)


class ReibunGenerator(object):
    def __init__(self, config):
        self.config = config

        self._prompt_manager = PromptManager(config)
        self.client = Anthropic(api_key=self.config.claude_api_key)

    def update_note_field(
        self,
        note,
        target_phrase,
        field_mappings,
        difficulty=None,
        generation_context=None,
        on_success_callback=None,
    ):
        response = self.generate_reibun(target_phrase, difficulty, generation_context)
        if not response:
            log.error("Failed when attempting to generate reibun.")
            return False

        for response_field, target_field in field_mappings.get(
            NoteConfig.FIELDS, {}
        ).items():
            note[target_field] = response[response_field]

        if on_success_callback:
            on_success_callback(note)

        return True

    def generate_reibun(self, target_phrase, difficulty=None, context=None):
        full_prompt = self._prompt_manager.build_reibun_prompt(
            target_phrase, difficulty=difficulty, context=context
        )
        log.info(estimate_reibun_cost(full_prompt))

        try:
            if self.config.debug_mode:
                response_content = get_example_return_value()
            else:
                response = self.client.messages.create(
                    model=MODEL,
                    max_tokens=300,
                    temperature=0.7,
                    messages=[{"role": "user", "content": full_prompt.strip()}],
                )
                response_content = response.content[0].text

            # Parse the response and extract relevant parts
            return self._parse_response(response_content)

        except Exception as e:
            print(f"Error generating example: {e}")
            return {}

    def _parse_response(self, response: str) -> Dict[str, str]:
        """Parse Claude's response into field values"""
        try:
            # Assuming response is in JSON format
            return json.loads(response)
        except:
            return {}

    def _build_prompt(self, word: str, context: dict) -> str:
        return dedent(f"""Generate a natural Japanese example sentence.

    Word Information:
    - Word: {word}

    Additional Context:
    {self._format_additional_context(context)}

    Generate a natural, everyday example sentence that demonstrates correct usage of this word or phrase.

    Format your response as JSON with the following fields:
    - sentence: The Japanese example sentence
    - reading: Reading in hiragana
    - translation: English translation
    - notes: Any relevant usage notes or explanations

    Important: Put <b>{word}</b> tags around the target word in both the sentence and reading.

    The sentence should be:
    - Natural, reflect real spoken/written Japanese, and be an ideal example sentence to learn from.
    - Not too long, ensure it's ideal for learning via spaced-repetition.
    - Appropriate for the word's level.
    - Clear in demonstrating the word's meaning and nuance.
    - Grammatically correct.
    """)

    def _format_additional_context(self, context: dict) -> str:
        # Filter out invalid options
        additional_context = {k: v for k, v in context.items() if v}
        additional_context_str = ""

        if NoteConfig.CONTEXT in additional_context:
            additional_context_str += ""

        return "\n".join(f"- {k}: {v}" for k, v in additional_context.items())


# Example usage with your Reibun generator
def estimate_reibun_cost(prompt: str):
    estimator = TokenCostEstimator()
    return estimator.estimate_cost(prompt, expected_output_length=200)


def get_example_return_value():
    json_string = """{
        "sentence": "試しに、この新しい料理を作ってみましょう。",
        "reading": "ためしに、このあたらしいりょうりをつくってみましょう。",
        "translation": "Let's try making this new dish.",
        "notes": "The word '試し' is used here as a particle to indicate that the speaker is suggesting trying or experimenting with something new. This usage is very common in everyday Japanese speech and writing."
    }"""
    return json_string

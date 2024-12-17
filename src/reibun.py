from typing import Dict

import json
import logging

from .dev.estimate import TokenCostEstimator

from anthropic import Anthropic

from .prompts.manager import PromptManager
from .constants import NoteConfig, ResponseFields


MODEL = "claude-3-haiku-20240307"
log = logging.getLogger(__name__)


class ReibunGenerationError(Exception):
    """Base exception for reibun generation errors."""

    pass


class ParsingError(ReibunGenerationError):
    """Raised when response parsing fails."""

    pass


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
    ):
        try:
            response = self._generate_reibun(
                target_phrase, difficulty=difficulty, context=generation_context
            )

            if not response:
                log.error("Failed when attempting to generate reibun.")
                return False

            for response_field, target_field in field_mappings.get(
                NoteConfig.FIELDS, {}
            ).items():
                note[target_field] = response[response_field]

        except Exception as e:
            log.error(f"Failed to update note: {e}")
            raise ReibunGenerationError(f"Failed to update note: {e}") from e

        return True

    def _generate_reibun(self, target_phrase, difficulty=None, context=None):
        full_prompt = self._prompt_manager.build_reibun_prompt(
            target_phrase, difficulty=difficulty, context=context
        )

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
            response_dict = self._parse_response(response_content)

            # Validate the response dictionary to ensure all required fields are present.
            self._validate_response(response_dict)

            return response_dict

        except Exception as e:
            print(f"Error generating example: {e}")
            return {}

    def _parse_response(self, response: str) -> Dict[str, str]:
        """Parse Claude's response into field values"""
        try:
            return json.loads(response)
        except json.decoder.JSONDecodeError as e:
            log.error(f"Failed to parse response: {e}", exc_info=True)
            raise ParsingError("Failed to parse LLM response") from e

    def _validate_response(self, response):
        missing = ResponseFields.required_fields - set(response.keys())
        if missing:
            raise ParsingError(f"Missing required fields: {missing}")


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

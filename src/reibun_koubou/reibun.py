from typing import List, Dict, Union
import tiktoken

import json
from textwrap import dedent

from .config import Config

from anthropic import Anthropic


MODEL = "claude-3-haiku-20240307"


class ReibunGenerator(object):
    def __init__(self):
        self.config = Config()
        self.client = Anthropic(api_key=self.config.claude_api_key)

    def update_note_field(
        self, note, target_phrase, target_field, context=None, on_success_callback=None
    ):
        response = self.generate_reibun(target_phrase, context=context)
        if not response:
            print("Failed when attempting to generate reibun.")
            return False

        note[target_field] = response["sentence"]
        if on_success_callback:
            on_success_callback(note)
        return True

    def generate_reibun(self, target_phrase, context=None):
        if context is None:
            context = {}

        prompt = self._build_prompt(target_phrase, context)
        print(estimate_reibun_cost(target_phrase))

        try:
            if self.config.debug_mode:
                response_content = get_example_return_value()
            else:
                response = self.client.messages.create(
                    model=MODEL,
                    max_tokens=300,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt.strip()}],
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
        additional_context = {k: v for k, v in context.items() if v}
        return "\n".join(f"- {k}: {v}" for k, v in additional_context.items())


class TokenCostEstimator:
    def __init__(self):
        # Initialize tokenizer for counting
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # Claude uses cl100k_base

        # Approximate costs per 1k tokens (as of April 2024)
        self.cost_per_1k = {
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.015, "output": 0.045},
            "claude-3-haiku": {"input": 0.015, "output": 0.03},
        }

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string"""
        return len(self.tokenizer.encode(text))

    def estimate_cost(
        self,
        prompt: Union[str, Dict, List],
        expected_output_length: int,
        model: str = MODEL,
    ) -> Dict[str, float]:
        """
        Estimate the cost of an API call

        Args:
            prompt: The prompt text or structured prompt
            expected_output_length: Expected number of tokens in response
            model: Model name to use for pricing

        Returns:
            Dictionary with token counts and estimated costs
        """
        # Convert prompt to string if it's a dict or list
        if isinstance(prompt, (dict, list)):
            prompt = json.dumps(prompt)

        input_tokens = self.count_tokens(prompt)

        # Get costs for the specified model
        model_costs = self.cost_per_1k.get(model, self.cost_per_1k["claude-3-haiku"])

        # Calculate costs
        input_cost = (input_tokens / 1000) * model_costs["input"]
        output_cost = (expected_output_length / 1000) * model_costs["output"]
        total_cost = input_cost + output_cost

        return {
            "input_tokens": input_tokens,
            "expected_output_tokens": expected_output_length,
            "total_tokens": input_tokens + expected_output_length,
            "input_cost": round(input_cost, 4),
            "output_cost": round(output_cost, 4),
            "total_cost": round(total_cost, 4),
            "model": model,
        }

    def estimate_batch_cost(
        self,
        number_of_requests: int,
        avg_prompt_tokens: int,
        avg_output_tokens: int,
        model: str = "claude-3-sonnet",
    ) -> Dict[str, float]:
        """
        Estimate the cost for a batch of similar requests

        Args:
            number_of_requests: Number of API calls planned
            avg_prompt_tokens: Average number of tokens per prompt
            avg_output_tokens: Average number of tokens per response
            model: Model name to use for pricing

        Returns:
            Dictionary with total token counts and estimated costs
        """
        model_costs = self.cost_per_1k.get(model, self.cost_per_1k["claude-3-sonnet"])

        total_input_tokens = avg_prompt_tokens * number_of_requests
        total_output_tokens = avg_output_tokens * number_of_requests

        input_cost = (total_input_tokens / 1000) * model_costs["input"]
        output_cost = (total_output_tokens / 1000) * model_costs["output"]
        total_cost = input_cost + output_cost

        return {
            "total_requests": number_of_requests,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens,
            "input_cost": round(input_cost, 4),
            "output_cost": round(output_cost, 4),
            "total_cost": round(total_cost, 4),
            "cost_per_request": round(total_cost / number_of_requests, 4),
            "model": model,
        }


# Example usage with your Reibun generator
def estimate_reibun_cost(word: str):
    estimator = TokenCostEstimator()

    # Build the same prompt as your generator would use
    prompt = f"""Generate a natural Japanese example sentence using the word "{word}".
              Please format the response as JSON with the following fields:
              - sentence: The Japanese example sentence
              - reading: Reading in hiragana
              - translation: English translation
              - notes: Any relevant usage notes"""

    # Estimate cost for a single generation
    # Assuming average response length of 200 tokens
    return estimator.estimate_cost(prompt, expected_output_length=200)


def get_example_return_value():
    json_string = """{
        "sentence": "試しに、この新しい料理を作ってみましょう。",
        "reading": "ためしに、このあたらしいりょうりをつくってみましょう。",
        "translation": "Let's try making this new dish.",
        "notes": "The word '試し' is used here as a particle to indicate that the speaker is suggesting trying or experimenting with something new. This usage is very common in everyday Japanese speech and writing."
    }"""
    return json_string

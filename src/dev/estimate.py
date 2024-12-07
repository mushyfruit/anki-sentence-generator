from typing import List, Dict, Union
import tiktoken

import json


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
        model: str = "claude-3-haiku",
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

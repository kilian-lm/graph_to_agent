"""OpenAI agent backend."""

import os
import logging
from typing import Optional

try:
    import requests
except ImportError:
    requests = None


class OpenAIAgent:
    """
    OpenAI API agent for executing chat completions.

    Example:
        agent = OpenAIAgent()
        response = agent.complete([
            {"role": "user", "content": "Hello!"}
        ])
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        base_url: str = "https://api.openai.com/v1/chat/completions",
        timeout: int = 60,
    ):
        """
        Initialize OpenAI agent.

        Args:
            api_key: API key (defaults to OPENAI_API_KEY env var)
            model: Model ID to use
            base_url: API endpoint
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    def complete(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Execute a chat completion.

        Args:
            messages: List of message dicts
            model: Model override
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Response content string
        """
        if not self.api_key:
            raise ValueError(
                "API key required. Set OPENAI_API_KEY or pass api_key parameter."
            )

        if requests is None:
            raise ImportError("requests library required: pip install requests")

        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        self.logger.debug(f"Calling OpenAI with {len(messages)} messages")

        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )

        if response.status_code != 200:
            self.logger.error(f"OpenAI error: {response.status_code} - {response.text}")
            response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    def stream(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
    ):
        """
        Stream a chat completion.

        Args:
            messages: List of message dicts
            model: Model override
            temperature: Sampling temperature

        Yields:
            Content chunks as they arrive
        """
        if not self.api_key:
            raise ValueError("API key required")

        if requests is None:
            raise ImportError("requests library required")

        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        import json

        with requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=self.timeout,
            stream=True,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                        except json.JSONDecodeError:
                            continue

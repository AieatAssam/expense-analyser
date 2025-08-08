import logging
import os
from typing import Any, Dict, Optional

import requests

from .llm_base import LLMProviderBase


class OpenAIProvider(LLMProviderBase):
    def send_request(self, prompt: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = params or {}
        # Preserve test behavior: if no API key, in test env, or endpoint isn't http(s), return mocked
        if (
            not self.api_key
            or os.getenv("ENVIRONMENT", "").lower() == "test"
            or not (self.endpoint.startswith("http://") or self.endpoint.startswith("https://"))
        ):
            logging.info("OpenAIProvider: Using mocked response (no API key or test env)")
            return {"provider": "openai", "response": "mocked response"}

        model = params.get("model", "gpt-4o-mini")
        messages = params.get("messages") or [{"role": "user", "content": prompt}]
        temperature = params.get("temperature", 0.2)
        timeout = params.get("timeout", 20)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }

        logging.info(f"OpenAIProvider: Sending request to {self.endpoint} with model={model}")
        try:
            resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            # Extract assistant message content
            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            if not content:
                # Fallback to plain text or first choice text fields if present
                content = data.get("choices", [{}])[0].get("text", "") or str(data)
            return {"provider": "openai", "response": content, "raw": data}
        except requests.RequestException as e:
            logging.error(f"OpenAIProvider: HTTP error - {e}")
            raise
        except Exception as e:
            logging.error(f"OpenAIProvider: Unexpected error - {e}")
            raise

import logging
from typing import Any, Dict, Optional

import openai

from .llm_base import LLMProviderBase

class OpenAIProvider(LLMProviderBase):
    def send_request(self, prompt: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        logging.info(f"OpenAIProvider: Sending request to {self.endpoint}")
        openai.api_key = self.api_key
        if self.endpoint:
            openai.api_base = self.endpoint

        model = (params or {}).get("model", "gpt-3.5-turbo")
        try:
            resp = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **{k: v for k, v in (params or {}).items() if k != "model"},
            )
            message = resp.choices[0].message["content"] if resp.choices else ""
            return {"provider": "openai", "response": message}
        except Exception as e:
            logging.error(f"OpenAIProvider error: {e}")
            raise

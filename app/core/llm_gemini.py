import logging
from typing import Any, Dict, Optional

import google.generativeai as genai

from .llm_base import LLMProviderBase

class GeminiProvider(LLMProviderBase):
    def send_request(self, prompt: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        logging.info(f"GeminiProvider: Sending request to {self.endpoint}")
        genai.configure(api_key=self.api_key)
        model_name = (params or {}).get("model", "gemini-pro")
        try:
            model = genai.GenerativeModel(model_name)
            resp = model.generate_content(prompt, **{k: v for k, v in (params or {}).items() if k != "model"})
            text = getattr(resp, "text", None)
            if text is None and hasattr(resp, "candidates") and resp.candidates:
                text = resp.candidates[0].content.parts[0].text
            return {"provider": "gemini", "response": text or ""}
        except Exception as e:
            logging.error(f"GeminiProvider error: {e}")
            raise

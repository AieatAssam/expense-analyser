import logging
import os
from typing import Any, Dict, Optional

import requests

from .llm_base import LLMProviderBase


class GeminiProvider(LLMProviderBase):
    def send_request(self, prompt: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = params or {}
        # Preserve test behavior: if no API key or in test env, return mocked
        if not self.api_key or os.getenv("ENVIRONMENT", "").lower() == "test":
            logging.info("GeminiProvider: Using mocked response (no API key or test env)")
            return {"provider": "gemini", "response": "mocked response"}

        # Support two styles: Google Generative Language API generateContent, or a simple chat endpoint
        model = params.get("model", "gemini-2.5-flash")
        timeout = params.get("timeout", 300)
        messages = params.get("messages")  # optional [{role, content}]

        # Build a best-effort payload compatible with "generateContent"
        if messages:
            # Flatten to text content blocks
            text = "\n".join(m.get("content", "") for m in messages)
        else:
            text = prompt

        # Build endpoint URL: allow template like .../models/{model}:generateContent
        endpoint = self.endpoint or ""
        try:
            url = endpoint.format(model=model) if "{model}" in endpoint else endpoint
        except Exception:
            url = endpoint
        # Ensure :generateContent is present (if a base models URL was provided)
        if ":generateContent" not in url:
            if url.endswith("/"):
                url = url.rstrip("/")
            # append action
            url = f"{url}:{'generateContent'}"
        # Append API key via query param
        if "key=" not in url:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}key={self.api_key}"

        # Build generation config with structured output default
        gen_config = params.get("generation_config", {}) if isinstance(params, dict) else {}
        if not isinstance(gen_config, dict):
            gen_config = {}
        gen_config.setdefault("responseMimeType", "application/json")

        # Build parts: always include text; optionally include inline image
        parts = [{"text": text}]
        image_b64 = (params or {}).get("image_data")
        image_fmt = (params or {}).get("image_format") or "jpeg"
        if image_b64:
            mime = f"image/{str(image_fmt).lower()}"
            # Normalize common extensions
            if mime == "image/jpg":
                mime = "image/jpeg"
            parts.append({
                "inline_data": {
                    "mime_type": mime,
                    "data": image_b64,
                }
            })

        payload = {
            "model": model,
            "contents": [
                {
                    "parts": parts,
                    "role": "user",
                }
            ],
            "generationConfig": gen_config,
        }

        headers = {"Content-Type": "application/json"}

        logging.info(f"GeminiProvider: Sending request to {url}")
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            # Extract text from candidates
            content = ""
            candidates = data.get("candidates") or []
            if candidates:
                parts = (
                    (candidates[0].get("content") or {}).get("parts") or []
                )
                if parts:
                    # parts can be [{'text': '...'}]
                    content = parts[0].get("text", "")
            if not content:
                content = str(data)
            return {"provider": "gemini", "response": content, "raw": data}
        except requests.RequestException as e:
            logging.error(f"GeminiProvider: HTTP error - {e}")
            raise
        except Exception as e:
            logging.error(f"GeminiProvider: Unexpected error - {e}")
            raise

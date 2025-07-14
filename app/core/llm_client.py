import os
import logging
from typing import Any, Dict, Optional
from .llm_gemini import GeminiProvider
from .llm_openai import OpenAIProvider

class LLMClient:
    def __init__(self, config: Optional[Dict[str, Any]] = None, provider_cls: Optional[type] = None):
        self.config = config or self._load_config()
        self.provider_name = self.config.get("provider", "gemini")
        self.provider_cls = provider_cls
        self.provider = self._init_provider()
        logging.basicConfig(level=logging.INFO)

    def _load_config(self) -> Dict[str, Any]:
        return {
            "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
            "gemini_endpoint": os.getenv("GEMINI_ENDPOINT", "https://gemini.googleapis.com/v1/chat"),
            "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
            "openai_endpoint": os.getenv("OPENAI_ENDPOINT", "https://api.openai.com/v1/chat/completions"),
            "provider": os.getenv("LLM_PROVIDER", "gemini"),
        }

    def _init_provider(self):
        if self.provider_cls:
            # Use injected provider class for testing or custom provider
            if self.provider_name == "gemini":
                return self.provider_cls(
                    api_key=self.config.get("gemini_api_key", ""),
                    endpoint=self.config.get("gemini_endpoint", "")
                )
            elif self.provider_name == "openai":
                return self.provider_cls(
                    api_key=self.config.get("openai_api_key", ""),
                    endpoint=self.config.get("openai_endpoint", "")
                )
            else:
                raise ValueError(f"Unsupported provider: {self.provider_name}")
        if self.provider_name == "gemini":
            return GeminiProvider(
                api_key=self.config["gemini_api_key"],
                endpoint=self.config["gemini_endpoint"]
            )
        elif self.provider_name == "openai":
            return OpenAIProvider(
                api_key=self.config["openai_api_key"],
                endpoint=self.config["openai_endpoint"]
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider_name}")

    def send(self, prompt: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        logging.info(f"LLMClient: Using provider {self.provider_name}")
        return self.provider.send_request(prompt, params)

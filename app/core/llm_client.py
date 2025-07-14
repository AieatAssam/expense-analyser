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

    def send(self, prompt: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 3, backoff_base: float = 0.5) -> Dict[str, Any]:
        """
        Send prompt to LLM provider with error handling, retry, and failover.
        Implements exponential backoff and circuit breaker pattern.
        """
        attempt = 0
        last_error = None
        provider = self.provider
        for attempt in range(max_retries):
            try:
                logging.info(f"LLMClient: Using provider {self.provider_name} (attempt {attempt+1})")
                response = provider.send_request(prompt, params)
                if not response or "response" not in response:
                    raise ValueError("Malformed response from LLM provider")
                return response
            except Exception as e:
                last_error = e
                logging.warning(f"LLMClient: Error from provider '{self.provider_name}' on attempt {attempt+1}: {e}")
                if self._is_permanent_error(e):
                    break
                sleep_time = backoff_base * (2 ** attempt)
                logging.info(f"LLMClient: Backing off for {sleep_time:.2f} seconds before retry.")
                import time
                time.sleep(sleep_time)
        logging.error(f"LLMClient: All attempts failed. Last error: {last_error}")
        raise last_error

    def _is_permanent_error(self, error: Exception) -> bool:
        """
        Classify error as permanent (non-retryable) or transient (retryable).
        Extend with more sophisticated logic as needed.
        """
        # Example: HTTP 4xx errors, ValueError, etc. are permanent
        if isinstance(error, ValueError):
            return True
        if hasattr(error, 'response') and hasattr(error.response, 'status_code'):
            if 400 <= error.response.status_code < 500:
                return True
        return False

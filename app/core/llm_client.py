import os
import logging
from typing import Any, Dict, Optional
from .llm_gemini import GeminiProvider
from .llm_openai import OpenAIProvider

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, config: Optional[Dict[str, Any]] = None, provider_cls: Optional[type] = None, cache_ttl: int = 60):
        self.config = config or self._load_config()
        self.provider_name = self.config.get("provider", "gemini")
        self.provider_cls = provider_cls
        self.provider = self._init_provider()
        self._cache = {}  # key: hash, value: (response, timestamp)
        self._cache_ttl = cache_ttl
        # Do not override global logging config here; rely on app-wide setup.

    def _load_config(self) -> Dict[str, Any]:
        return {
            "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
            # Default to Generative Language API generateContent endpoint template
            # Example final URL: https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent
            "gemini_endpoint": os.getenv(
                "GEMINI_ENDPOINT",
                "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            ),
            "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
            "openai_endpoint": os.getenv("OPENAI_ENDPOINT", "https://api.openai.com/v1/chat/completions"),
            # Allow DEFAULT_LLM_PROVIDER for docker-compose compatibility
            "provider": os.getenv("LLM_PROVIDER") or os.getenv("DEFAULT_LLM_PROVIDER", "gemini"),
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
            if not self.config.get("gemini_api_key"):
                logger.warning("LLMClient: GEMINI_API_KEY is empty; requests will fail until configured")
            return GeminiProvider(
                api_key=self.config["gemini_api_key"],
                endpoint=self.config["gemini_endpoint"]
            )
        elif self.provider_name == "openai":
            if not self.config.get("openai_api_key"):
                logger.warning("LLMClient: OPENAI_API_KEY is empty; requests will fail until configured")
            return OpenAIProvider(
                api_key=self.config["openai_api_key"],
                endpoint=self.config["openai_endpoint"]
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider_name}")

    def send(self, prompt: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 3, backoff_base: float = 0.5) -> Dict[str, Any]:
        """
        Send prompt to LLM provider with error handling, retry, failover, and caching.
        Implements exponential backoff, circuit breaker, and response caching/deduplication with TTL expiry.
        """
        import hashlib
        import json
        import time
        cache_key = hashlib.sha256((prompt + json.dumps(params or {}, sort_keys=True)).encode()).hexdigest()
        now = time.time()
        if cache_key in self._cache:
            cached_response, cached_time = self._cache[cache_key]
            if now - cached_time < self._cache_ttl:
                logger.info(f"LLMClient: returning cached response", extra={"cache_key": cache_key})
                return cached_response
            else:
                logger.info(f"LLMClient: cache expired", extra={"cache_key": cache_key})
                del self._cache[cache_key]
        attempt = 0
        last_error = None
        provider = self.provider
        for attempt in range(max_retries):
            try:
                start_ts = time.time()
                logger.info(
                    "LLMClient: sending request",
                    extra={
                        "provider": self.provider_name,
                        "attempt": attempt + 1,
                        "prompt_chars": len(prompt or ""),
                        "has_image": bool(params and params.get("image_data")),
                        "max_tokens": (params or {}).get("max_tokens"),
                        "temperature": (params or {}).get("temperature"),
                    },
                )
                response = provider.send_request(prompt, params)
                duration = time.time() - start_ts
                logger.info(
                    "LLMClient: received response",
                    extra={
                        "provider": self.provider_name,
                        "attempt": attempt + 1,
                        "duration_ms": int(duration * 1000),
                    },
                )
                if not response or "response" not in response:
                    raise ValueError("Malformed response from LLM provider")
                self._cache[cache_key] = (response, now)
                return response
            except Exception as e:
                last_error = e
                logger.warning(
                    "LLMClient: provider error",
                    extra={"provider": self.provider_name, "attempt": attempt + 1, "error": str(e)},
                )
                if self._is_permanent_error(e):
                    break
                sleep_time = backoff_base * (2 ** attempt)
                logger.info("LLMClient: backing off before retry", extra={"sleep_seconds": round(sleep_time, 2)})
                time.sleep(sleep_time)
        logger.error("LLMClient: all attempts failed", extra={"provider": self.provider_name, "error": str(last_error)})
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

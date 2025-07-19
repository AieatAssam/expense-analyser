import os
import logging
import hashlib
import json
import time
import redis
from typing import Any, Dict, Optional, Tuple, List
from .llm_base import LLMProviderBase
from .llm_gemini import GeminiProvider
from .llm_openai import OpenAIProvider

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LLMClient")

class LLMClient:
    """
    Client for interfacing with LLM providers with robust error handling, caching, and failover.
    Features:
    - Configurable primary and fallback providers (default: Gemini primary, OpenAI fallback)
    - Exponential backoff retry strategy
    - Circuit breaker pattern to detect provider health
    - Response caching with TTL
    - Request deduplication
    - Provider failover on persistent errors
    """
    
    def __init__(self, 
                 config: Optional[Dict[str, Any]] = None, 
                 provider_cls: Optional[type] = None, 
                 cache_ttl: int = 60,
                 use_redis_cache: bool = False):
        self.config = config or self._load_config()
        self.provider_name = self.config.get("provider", "gemini")
        self.fallback_provider_name = "openai" if self.provider_name == "gemini" else "gemini"
        self.provider_cls = provider_cls
        self.provider = self._init_provider(self.provider_name)
        self.fallback_provider = self._init_provider(self.fallback_provider_name)
        
        # Cache configuration
        self._cache_ttl = cache_ttl
        self._use_redis_cache = use_redis_cache and self.config.get("redis_url")
        
        # Initialize cache
        self._cache = {}  # key: hash, value: (response, timestamp)
        
        if self._use_redis_cache:
            try:
                self._redis = redis.Redis.from_url(
                    self.config.get("redis_url", "redis://localhost:6379/0"),
                    decode_responses=False
                )
                logger.info("Redis cache initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis cache: {e}. Falling back to in-memory cache.")
                self._use_redis_cache = False
        
        # Circuit breaker configuration
        self._circuit_breaker = {
            "gemini": {"failures": 0, "last_failure": 0, "open": False},
            "openai": {"failures": 0, "last_failure": 0, "open": False}
        }
        self._failure_threshold = self.config.get("failure_threshold", 3)
        self._circuit_reset_time = self.config.get("circuit_reset_time", 300)  # 5 minutes

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        return {
            "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
            "gemini_endpoint": os.getenv("GEMINI_ENDPOINT", "https://generativelanguage.googleapis.com/v1/models"),
            "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
            "openai_endpoint": os.getenv("OPENAI_ENDPOINT", "https://api.openai.com/v1"),
            "provider": os.getenv("LLM_PROVIDER", "gemini"),
            "redis_url": os.getenv("REDIS_URL", ""),
            "failure_threshold": int(os.getenv("LLM_FAILURE_THRESHOLD", "3")),
            "circuit_reset_time": int(os.getenv("LLM_CIRCUIT_RESET_TIME", "300")),
        }

    def _init_provider(self, provider_name: str) -> LLMProviderBase:
        """Initialize a provider instance based on name and configuration."""
        if self.provider_cls:
            # Use injected provider class for testing or custom provider
            if provider_name == "gemini":
                return self.provider_cls(
                    api_key=self.config.get("gemini_api_key", ""),
                    endpoint=self.config.get("gemini_endpoint", "")
                )
            elif provider_name == "openai":
                return self.provider_cls(
                    api_key=self.config.get("openai_api_key", ""),
                    endpoint=self.config.get("openai_endpoint", "")
                )
            else:
                raise ValueError(f"Unsupported provider: {provider_name}")
                
        # Initialize actual provider
        if provider_name == "gemini":
            return GeminiProvider(
                api_key=self.config["gemini_api_key"],
                endpoint=self.config["gemini_endpoint"]
            )
        elif provider_name == "openai":
            return OpenAIProvider(
                api_key=self.config["openai_api_key"],
                endpoint=self.config["openai_endpoint"]
            )
        else:
            raise ValueError(f"Unsupported provider: {provider_name}")

    def send(self, 
             prompt: str, 
             params: Optional[Dict[str, Any]] = None, 
             max_retries: int = 3, 
             backoff_base: float = 0.5,
             skip_cache: bool = False) -> Dict[str, Any]:
        """
        Send prompt to LLM provider with error handling, retry, failover, and caching.
        
        Args:
            prompt: The prompt to send to the LLM provider
            params: Additional parameters to pass to the provider
            max_retries: Maximum number of retry attempts
            backoff_base: Base delay for exponential backoff
            skip_cache: Whether to skip cache lookup
            
        Returns:
            Dict containing the LLM provider response
            
        Raises:
            Exception: If all attempts with all providers fail
        """
        # Generate cache key from prompt and params
        cache_key = self._generate_cache_key(prompt, params)
        
        # Check cache if not skipping
        if not skip_cache:
            cached_response = self._get_from_cache(cache_key)
            if cached_response:
                logger.info(f"Returning cached response for key {cache_key[:8]}...")
                return cached_response
        
        # First try primary provider with retries
        result, error = self._try_provider(
            self.provider_name, 
            self.provider, 
            prompt, 
            params, 
            max_retries, 
            backoff_base
        )
        
        # If successful, cache and return the result
        if result:
            self._set_in_cache(cache_key, result)
            return result
            
        # If primary provider failed, check circuit breaker status for fallback
        if self._circuit_breaker[self.fallback_provider_name]["open"]:
            # Fallback circuit is open, check if it's time to reset
            if time.time() - self._circuit_breaker[self.fallback_provider_name]["last_failure"] > self._circuit_reset_time:
                logger.info(f"Resetting circuit breaker for {self.fallback_provider_name}")
                self._circuit_breaker[self.fallback_provider_name]["open"] = False
            else:
                logger.warning(f"Circuit open for fallback provider {self.fallback_provider_name}. Raising error.")
                raise error
                
        # Try fallback provider with retries
        logger.info(f"Failing over to {self.fallback_provider_name} provider")
        result, fallback_error = self._try_provider(
            self.fallback_provider_name,
            self.fallback_provider,
            prompt,
            params,
            max_retries,
            backoff_base
        )
        
        # If successful with fallback, cache and return
        if result:
            self._set_in_cache(cache_key, result)
            return result
            
        # Both providers failed
        logger.error(f"All providers failed. Primary error: {error}, Fallback error: {fallback_error}")
        raise fallback_error

    def _try_provider(self, 
                     provider_name: str, 
                     provider: LLMProviderBase, 
                     prompt: str, 
                     params: Optional[Dict[str, Any]], 
                     max_retries: int, 
                     backoff_base: float) -> Tuple[Optional[Dict[str, Any]], Optional[Exception]]:
        """
        Try sending the prompt to a specific provider with retries.
        Returns (response, None) on success or (None, error) on failure.
        """
        # Check circuit breaker
        if self._circuit_breaker[provider_name]["open"]:
            # If circuit is open, check if it's time to reset
            if time.time() - self._circuit_breaker[provider_name]["last_failure"] > self._circuit_reset_time:
                logger.info(f"Resetting circuit breaker for {provider_name}")
                self._circuit_breaker[provider_name]["open"] = False
                self._circuit_breaker[provider_name]["failures"] = 0
            else:
                logger.warning(f"Circuit open for provider {provider_name}. Skipping.")
                return None, ValueError(f"Circuit breaker open for {provider_name}")
                
        # Try provider with retries
        last_error = None
        for attempt in range(max_retries):
            try:
                logger.info(f"Using provider {provider_name} (attempt {attempt+1})")
                response = provider.send_request(prompt, params)
                
                # Validate response
                if not response or "response" not in response:
                    raise ValueError(f"Malformed response from {provider_name} provider")
                    
                # Reset circuit breaker on success
                self._circuit_breaker[provider_name]["failures"] = 0
                self._circuit_breaker[provider_name]["open"] = False
                
                return response, None
                
            except Exception as e:
                last_error = e
                logger.warning(f"Error from provider '{provider_name}' on attempt {attempt+1}: {e}")
                
                # Update circuit breaker
                if self._is_permanent_error(e):
                    self._circuit_breaker[provider_name]["failures"] += 1
                    self._circuit_breaker[provider_name]["last_failure"] = time.time()
                    
                    # Check if failure threshold is reached
                    if self._circuit_breaker[provider_name]["failures"] >= self._failure_threshold:
                        logger.warning(f"Circuit breaker opened for {provider_name} after {self._failure_threshold} failures")
                        self._circuit_breaker[provider_name]["open"] = True
                        break
                        
                    # Don't retry permanent errors
                    break
                    
                # Apply exponential backoff for transient errors
                sleep_time = backoff_base * (2 ** attempt)
                logger.info(f"Backing off for {sleep_time:.2f} seconds before retry.")
                time.sleep(sleep_time)
                
        # All attempts failed
        logger.error(f"All attempts with {provider_name} failed. Last error: {last_error}")
        return None, last_error

    def _is_permanent_error(self, error: Exception) -> bool:
        """
        Classify error as permanent (non-retryable) or transient (retryable).
        """
        # Authentication and input validation errors are permanent
        if isinstance(error, ValueError):
            return True
            
        # API-specific errors that indicate invalid requests
        if hasattr(error, 'response') and hasattr(error.response, 'status_code'):
            # 400 Bad Request, 401 Unauthorized, 403 Forbidden are permanent
            if error.response.status_code in (400, 401, 403, 404):
                return True
                
        # OpenAI-specific errors
        if hasattr(error, 'code'):
            # Invalid API key, invalid parameters, etc.
            if error.code in ('invalid_api_key', 'invalid_request_error'):
                return True
                
        # Rate limit errors are transient
        if "rate limit" in str(error).lower() or "429" in str(error):
            return False
            
        # Server errors are transient
        if any(code in str(error) for code in ('500', '502', '503', '504')):
            return False
            
        # Default to considering it permanent for safety
        return True
        
    def _generate_cache_key(self, prompt: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Generate a cache key from prompt and parameters."""
        cache_input = prompt + json.dumps(params or {}, sort_keys=True)
        return hashlib.sha256(cache_input.encode()).hexdigest()
        
    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a response from cache (either Redis or in-memory)."""
        now = time.time()
        
        # Redis cache
        if self._use_redis_cache:
            try:
                data = self._redis.get(f"llm_cache:{key}")
                if data:
                    cached_response, cached_time = json.loads(data)
                    if now - cached_time < self._cache_ttl:
                        return cached_response
                    else:
                        # Cache has expired
                        self._redis.delete(f"llm_cache:{key}")
                        return None  # Explicitly return None for expired cache
            except Exception as e:
                logger.warning(f"Redis cache error: {e}. Falling back to in-memory cache.")
                self._use_redis_cache = False
                
        # In-memory cache
        if key in self._cache:  # Changed 'elif' to 'if' to handle fallback from Redis
            cached_response, cached_time = self._cache[key]
            if now - cached_time < self._cache_ttl:
                return cached_response
            else:
                # Cache has expired
                del self._cache[key]
                return None  # Explicitly return None for expired cache
                
        return None
        
    def _set_in_cache(self, key: str, value: Dict[str, Any]) -> None:
        """Store a response in cache (either Redis or in-memory)."""
        now = time.time()
        
        # Redis cache
        if self._use_redis_cache:
            try:
                self._redis.setex(
                    f"llm_cache:{key}",
                    self._cache_ttl,
                    json.dumps((value, now))
                )
                return
            except Exception as e:
                logger.warning(f"Redis cache error: {e}. Falling back to in-memory cache.")
                self._use_redis_cache = False
                
        # In-memory cache
        self._cache[key] = (value, now)

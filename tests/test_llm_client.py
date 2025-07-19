import pytest
from unittest.mock import patch, MagicMock
import time
from app.core.llm_client import LLMClient

class DummyProvider:
    """Basic provider that returns the prompt as the response"""
    def __init__(self, api_key, endpoint):
        self.api_key = api_key
        self.endpoint = endpoint
        self.name = "dummy"
        
    def send_request(self, prompt, params=None):
        return {"provider": self.name, "response": prompt}

class GeminiDummyProvider(DummyProvider):
    """Gemini-specific dummy provider"""
    def __init__(self, api_key, endpoint):
        super().__init__(api_key, endpoint)
        self.name = "gemini"

class OpenAIDummyProvider(DummyProvider):
    """OpenAI-specific dummy provider"""
    def __init__(self, api_key, endpoint):
        super().__init__(api_key, endpoint)
        self.name = "openai"

class TransientErrorProvider:
    """Provider that fails with transient errors a specified number of times then succeeds"""
    def __init__(self, api_key, endpoint, fail_count=1):
        self.api_key = api_key
        self.endpoint = endpoint
        self.calls = 0
        self.fail_count = fail_count
        self.name = "transient-error-provider"
        
    def send_request(self, prompt, params=None):
        self.calls += 1
        if self.calls <= self.fail_count:
            # Create an error that will be classified as transient
            error = RuntimeError(f"Transient error (attempt {self.calls})")
            if hasattr(error, 'response'):
                error.response.status_code = 503  # Service Unavailable
            raise error
        return {"provider": self.name, "response": prompt, "attempts": self.calls}

class PermanentErrorProvider:
    """Provider that always fails with a permanent error"""
    def __init__(self, api_key, endpoint):
        self.api_key = api_key
        self.endpoint = endpoint
        self.name = "permanent-error-provider"
        
    def send_request(self, prompt, params=None):
        raise ValueError("Permanent error")

@pytest.fixture
def mock_redis():
    """Fixture to mock Redis"""
    with patch('app.core.llm_client.redis.Redis') as mock:
        mock_instance = MagicMock()
        mock.from_url.return_value = mock_instance
        yield mock_instance

def test_llmclient_gemini():
    """Test client with Gemini provider"""
    client = LLMClient({
        "gemini_api_key": "fake-key",
        "gemini_endpoint": "fake-endpoint",
        "provider": "gemini"
    }, provider_cls=GeminiDummyProvider)
    result = client.send("success")
    assert result["provider"] == "gemini"
    assert result["response"] == "success"

def test_llmclient_openai():
    """Test client with OpenAI provider"""
    client = LLMClient({
        "openai_api_key": "fake-key",
        "openai_endpoint": "fake-endpoint",
        "provider": "openai"
    }, provider_cls=OpenAIDummyProvider)
    result = client.send("success")
    assert result["provider"] == "openai"
    assert result["response"] == "success"

def test_llmclient_retry_success():
    """Test retrying with transient errors"""
    # Create a custom provider that works on the second attempt
    class RetryTestProvider:
        def __init__(self, api_key, endpoint):
            self.api_key = api_key
            self.endpoint = endpoint
            self.calls = 0
            
        def send_request(self, prompt, params=None):
            self.calls += 1
            if self.calls == 1:
                # First call fails but is classified as transient
                raise ConnectionError("Connection error (transient)")
            # Second call succeeds
            return {"provider": "retry-test", "response": prompt, "attempts": self.calls}
            
    # Patch the _is_permanent_error method to make our error transient
    client = LLMClient({
        "gemini_api_key": "fake-key",
        "gemini_endpoint": "fake-endpoint",
        "openai_api_key": "fake-key",  # Add OpenAI config to avoid KeyError
        "openai_endpoint": "fake-endpoint",  # Add OpenAI endpoint
        "provider": "gemini"
    })
    
    # Replace both providers with our test provider
    client.provider = RetryTestProvider("fake-key", "fake-endpoint")
    client.fallback_provider = RetryTestProvider("fake-key", "fake-endpoint")
    
    # Add a method to override error classification
    client._is_permanent_error = lambda e: False
    
    # Backoff time of 0 for faster tests
    result = client.send("retry-success", max_retries=3, backoff_base=0)
    
    assert result["provider"] == "retry-test"
    assert result["response"] == "retry-success"
    assert result["attempts"] == 2  # First attempt failed, second succeeded

def test_llmclient_permanent_error_no_fallback():
    """Test handling permanent errors without fallback"""
    # Create a client with both providers having permanent errors
    client = LLMClient({
        "gemini_api_key": "fake-key",
        "gemini_endpoint": "fake-endpoint",
        "provider": "gemini",
        "openai_api_key": "fake-key",
        "openai_endpoint": "fake-endpoint",
    }, provider_cls=PermanentErrorProvider)
    
    # Should raise the error since both providers would fail
    with pytest.raises(ValueError) as excinfo:
        client.send("fail", max_retries=1)
    
    assert "Permanent error" in str(excinfo.value)

def test_llmclient_failover_to_openai():
    """Test failover from Gemini to OpenAI"""
    # Create a client with primary provider (Gemini) failing and fallback (OpenAI) working
    def provider_factory(api_key, endpoint):
        if "gemini" in api_key or "gemini" in endpoint:
            return PermanentErrorProvider(api_key, endpoint)
        return OpenAIDummyProvider(api_key, endpoint)
    
    client = LLMClient({
        "gemini_api_key": "gemini-key",
        "gemini_endpoint": "gemini-endpoint",
        "openai_api_key": "openai-key",
        "openai_endpoint": "openai-endpoint",
        "provider": "gemini"
    }, provider_cls=provider_factory)
    
    result = client.send("failover-test", max_retries=1)
    assert result["provider"] == "openai"
    assert result["response"] == "failover-test"

def test_llmclient_circuit_breaker(monkeypatch):
    """Test circuit breaker opens after threshold failures"""
    # Mock time to control circuit breaker timing
    monkeypatch.setattr(time, "time", lambda: 1000)
    
    # Provider that always fails with a permanent error
    client = LLMClient({
        "gemini_api_key": "fake-key",
        "gemini_endpoint": "fake-endpoint",
        "provider": "gemini",
        "failure_threshold": 2  # Circuit opens after 2 failures
    }, provider_cls=PermanentErrorProvider)
    
    # First failure
    with pytest.raises(ValueError):
        client.send("fail1", max_retries=1)
    
    # Circuit should not be open yet
    assert client._circuit_breaker["gemini"]["failures"] == 1
    assert client._circuit_breaker["gemini"]["open"] is False
    
    # Second failure should open the circuit
    with pytest.raises(ValueError):
        client.send("fail2", max_retries=1)
    
    # Circuit should now be open
    assert client._circuit_breaker["gemini"]["failures"] == 2
    assert client._circuit_breaker["gemini"]["open"] is True

def test_llmclient_circuit_reset(monkeypatch):
    """Test circuit breaker reset after reset_time passes"""
    # Use a counter for the mock time instead of a list that can be emptied
    time_counter = [0]  # Using a list to make it mutable within the lambda
    
    def mock_time():
        if time_counter[0] == 0:
            time_counter[0] = 1000  # Initial time
            return 1000
        elif time_counter[0] == 1000:
            time_counter[0] = 1301  # Time after reset period
            return 1000
        else:
            return 1301  # Any subsequent calls
    
    monkeypatch.setattr(time, "time", mock_time)
    
    # Create client with short circuit reset time
    client = LLMClient({
        "gemini_api_key": "fake-key",
        "gemini_endpoint": "fake-endpoint",
        "provider": "gemini",
        "failure_threshold": 1,  # Circuit opens after 1 failure
        "circuit_reset_time": 300  # 5 minutes
    }, provider_cls=PermanentErrorProvider)
    
    # First failure opens circuit
    with pytest.raises(Exception):
        client.send("fail", max_retries=1)
    
    # Circuit should be open
    assert client._circuit_breaker["gemini"]["open"] is True
    
    # Now replace provider with working one and also the fallback
    client.provider = DummyProvider("fake-key", "fake-endpoint")
    client.fallback_provider = DummyProvider("fake-key", "fake-endpoint")
    
    # Try again after reset time, should work as circuit is reset
    result = client.send("success")
    assert "provider" in result
    assert "response" in result
    assert result["response"] == "success"
    
    # Circuit should be reset after the successful call
    assert client._circuit_breaker["gemini"]["failures"] == 0

def test_llmclient_redis_cache(mock_redis):
    """Test Redis cache functionality"""
    # Setup client with Redis cache
    client = LLMClient({
        "gemini_api_key": "fake-key",
        "gemini_endpoint": "fake-endpoint",
        "provider": "gemini",
        "redis_url": "redis://localhost:6379/0"
    }, provider_cls=DummyProvider, use_redis_cache=True)
    
    # First request should go through and be cached
    mock_redis.get.return_value = None  # No cached value
    
    result = client.send("cache-test")
    assert result["provider"] == "dummy"
    assert result["response"] == "cache-test"
    
    # Check that response was stored in cache
    mock_redis.setex.assert_called_once()
    
    # Now simulate cached response
    import json
    mock_redis.get.return_value = json.dumps(({"provider": "cached", "response": "from-cache"}, time.time())).encode()
    
    # Second request with same prompt should return cached value
    result = client.send("cache-test")
    assert result["provider"] == "cached"
    assert result["response"] == "from-cache"

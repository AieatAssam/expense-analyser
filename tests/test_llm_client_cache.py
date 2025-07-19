import time
from app.core.llm_client import LLMClient

class DummyProvider:
    def __init__(self, api_key, endpoint):
        self.calls = 0
    def send_request(self, prompt, params=None):  # This line is valid and should remain
        self.calls += 1
        return {"provider": "dummy", "response": prompt, "calls": self.calls}

def test_llmclient_caching():
    client = LLMClient({"provider": "gemini"}, provider_cls=DummyProvider)
    result1 = client.send("cache-test", params={"a": 1})
    result2 = client.send("cache-test", params={"a": 1})
    assert result1 == result2
    assert result1["calls"] == 1  # Only one actual call

def test_llmclient_deduplication():
    client = LLMClient({"provider": "gemini"}, provider_cls=DummyProvider)
    result1 = client.send("dedupe-test", params={"x": 2})
    result2 = client.send("dedupe-test", params={"x": 2})
    assert result1 == result2
    assert result1["calls"] == 1

def test_llmclient_cache_key_differs():
    client = LLMClient({"provider": "gemini"}, provider_cls=DummyProvider)
    result1 = client.send("diff-test", params={"x": 2})
    result2 = client.send("diff-test", params={"x": 3})
    assert result1 != result2
    assert result1["calls"] == 1
    assert result2["calls"] == 2

def test_llmclient_cache_expiry():
    """Test that cached responses expire after TTL and trigger new provider calls."""
    # Use a simpler approach - directly manipulate the cache
    
    # Call counter for our dummy provider
    call_count = 0
    
    class TestProvider:
        def __init__(self, *args, **kwargs):
            pass
        
        def send_request(self, prompt, params=None):
            nonlocal call_count
            call_count += 1
            return {"provider": "test", "response": prompt, "call": call_count}
    
    # Create client with short cache TTL
    client = LLMClient({"provider": "gemini"}, provider_cls=TestProvider, cache_ttl=10)
    
    # First call - should call provider
    result1 = client.send("test-expiry", params={"x": 1})
    assert call_count == 1
    assert result1["call"] == 1
    
    # Second immediate call - should use cache
    result2 = client.send("test-expiry", params={"x": 1})
    assert call_count == 1  # No new provider call
    assert result2["call"] == 1  # Same result as before
    
    # Manually expire the cache by manipulating the timestamp
    cache_key = client._generate_cache_key("test-expiry", {"x": 1})
    if cache_key in client._cache:
        response, old_time = client._cache[cache_key]
        # Set timestamp to 20 seconds ago (beyond the 10s TTL)
        client._cache[cache_key] = (response, old_time - 20)
    
    # Call again - should detect expired cache and call provider again
    result3 = client.send("test-expiry", params={"x": 1})
    assert call_count == 2  # New provider call
    assert result3["call"] == 2  # New result

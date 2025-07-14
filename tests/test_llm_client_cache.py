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

def test_llmclient_cache_expiry(monkeypatch):
    times = [1000, 1001, 1062]  # Simulate time progression
    def fake_time():
        return times.pop(0)
    client = LLMClient({"provider": "gemini"}, provider_cls=DummyProvider, cache_ttl=60)
    monkeypatch.setattr("time.time", fake_time)
    result1 = client.send("expire-test", params={"x": 1})
    result2 = client.send("expire-test", params={"x": 1})
    assert result1 == result2
    assert result1["calls"] == 1
    # After TTL expires, should call provider again
    result3 = client.send("expire-test", params={"x": 1})
    assert result3["calls"] == 2

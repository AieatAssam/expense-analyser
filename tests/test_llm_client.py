import pytest
from app.core.llm_client import LLMClient

class DummyProvider:
    def __init__(self, api_key, endpoint):
        pass
    def send_request(self, prompt, params=None):
        return {"provider": "dummy", "response": prompt}

def test_llmclient_gemini():
    client = LLMClient({
        "gemini_api_key": "",
        "gemini_endpoint": "",
        "provider": "gemini"
    }, provider_cls=DummyProvider)
    result = client.send("success")
    assert result["provider"] == "dummy"
    assert result["response"] == "success"

def test_llmclient_openai():
    client = LLMClient({
        "openai_api_key": "",
        "openai_endpoint": "",
        "provider": "openai"
    }, provider_cls=DummyProvider)
    result = client.send("success")
    assert result["provider"] == "dummy"
    assert result["response"] == "success"

def test_llmclient_retry_and_failover(monkeypatch):
    class FailingProvider:
        def __init__(self, api_key, endpoint):
            self.calls = 0
        def send_request(self, prompt, params=None):
            self.calls += 1
            if self.calls < 2:
                raise Exception("Transient error")
            return {"provider": "dummy", "response": prompt}
    client = LLMClient({
        "gemini_api_key": "",
        "gemini_endpoint": "",
        "provider": "gemini"
    }, provider_cls=FailingProvider)
    result = client.send("retry-success", max_retries=3)
    assert result["provider"] == "dummy"
    assert result["response"] == "retry-success"

    # Permanent error triggers circuit breaker
    class PermanentErrorProvider:
        def __init__(self, api_key, endpoint):
            pass
        def send_request(self, prompt, params=None):
            raise ValueError("Permanent error")
    client = LLMClient({
        "gemini_api_key": "",
        "gemini_endpoint": "",
        "provider": "gemini"
    }, provider_cls=PermanentErrorProvider)
    with pytest.raises(ValueError):
        client.send("fail", max_retries=3)

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

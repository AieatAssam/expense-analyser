import pytest
from app.core.llm_base import LLMProviderBase

class DummyProvider(LLMProviderBase):
    def send_request(self, prompt, params=None):
        return {"provider": "dummy", "response": prompt}

def test_llmproviderbase_abstract():
    with pytest.raises(TypeError):
        LLMProviderBase(api_key="key", endpoint="url")

def test_dummyprovider_send_request():
    provider = DummyProvider(api_key="key", endpoint="url")
    result = provider.send_request("test-prompt")
    assert result["provider"] == "dummy"
    assert result["response"] == "test-prompt"

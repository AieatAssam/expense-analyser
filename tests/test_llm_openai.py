from app.core.llm_openai import OpenAIProvider

def test_openai_provider_mock(monkeypatch):
    provider = OpenAIProvider(api_key="fake-key", endpoint="fake-endpoint")
    result = provider.send_request("test-prompt")
    assert result["provider"] == "openai"
    assert "mocked response" in result["response"]

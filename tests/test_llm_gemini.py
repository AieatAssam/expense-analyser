from app.core.llm_gemini import GeminiProvider

def test_gemini_provider_mock(monkeypatch):
    provider = GeminiProvider(api_key="fake-key", endpoint="fake-endpoint")
    result = provider.send_request("test-prompt")
    assert result["provider"] == "gemini"
    assert "mocked response" in result["response"]

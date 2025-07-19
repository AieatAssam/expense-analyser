import pytest
from unittest.mock import patch, MagicMock
from app.core.llm_gemini import GeminiProvider

@pytest.fixture
def mock_genai():
    with patch('app.core.llm_gemini.genai') as mock:
        # Create a mock response structure similar to what Gemini returns
        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content = MagicMock()
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].text = '{"store_name": "Test Store", "date": "2025-07-01", "total_amount": 10.0, "line_items": [{"name": "Test Item", "category": "Test", "amount": 10.0}]}'
        
        # Set up the mock GenerativeModel to return our mock response
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock.GenerativeModel.return_value = mock_model
        
        # Configure the mock
        mock.configure = MagicMock()
        
        yield mock

def test_gemini_provider_initialization(mock_genai):
    provider = GeminiProvider(api_key="fake-key", endpoint="fake-endpoint")
    mock_genai.configure.assert_called_once_with(api_key="fake-key")
    assert provider.model_name == "gemini-1.5-flash"

def test_gemini_provider_send_request(mock_genai):
    provider = GeminiProvider(api_key="fake-key", endpoint="fake-endpoint")
    result = provider.send_request("test-prompt")
    
    # Verify the model was created correctly
    mock_genai.GenerativeModel.assert_called_once_with("gemini-1.5-flash")
    
    # Verify generate_content was called with the prompt
    mock_model = mock_genai.GenerativeModel.return_value
    mock_model.generate_content.assert_called_once()
    args, kwargs = mock_model.generate_content.call_args
    assert args[0] == "test-prompt"
    
    # Check the response
    assert result["provider"] == "gemini"
    assert result["model"] == "gemini-1.5-flash"
    assert "store_name" in result["response"]
    assert result["response"]["store_name"] == "Test Store"

def test_gemini_provider_with_params(mock_genai):
    provider = GeminiProvider(api_key="fake-key", endpoint="fake-endpoint")
    params = {"model": "gemini-1.5-pro", "temperature": 0.1, "max_tokens": 1000}
    result = provider.send_request("test-prompt", params)
    
    # Verify the model was created with the specified name
    mock_genai.GenerativeModel.assert_called_once_with("gemini-1.5-pro")
    
    # Check if temperature was updated
    assert provider.generation_config["temperature"] == 0.1
    
    # Check if max_tokens was updated
    assert provider.generation_config["max_output_tokens"] == 1000

def test_gemini_provider_json_extraction(mock_genai):
    # Test with JSON embedded in markdown code blocks
    markdown_response = "```json\n{\"key\": \"value\"}\n```"
    mock_genai.GenerativeModel.return_value.generate_content.return_value.candidates[0].content.parts[0].text = markdown_response
    
    provider = GeminiProvider(api_key="fake-key", endpoint="fake-endpoint")
    result = provider.send_request("test-prompt")
    
    assert result["response"] == {"key": "value"}

def test_gemini_provider_error_handling(mock_genai):
    # Test API error handling
    mock_genai.GenerativeModel.return_value.generate_content.side_effect = Exception("Rate limit exceeded")
    
    provider = GeminiProvider(api_key="fake-key", endpoint="fake-endpoint")
    with pytest.raises(Exception) as excinfo:
        provider.send_request("test-prompt")
        
    assert "Rate limit" in str(excinfo.value)

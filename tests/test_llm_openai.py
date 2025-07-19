import pytest
from unittest.mock import patch, MagicMock
from app.core.llm_openai import OpenAIProvider

@pytest.fixture
def mock_openai():
    with patch('app.core.llm_openai.openai') as mock:
        # Create a mock ChatCompletion structure
        mock_message = MagicMock()
        mock_message.content = '{"store_name": "Test Store", "date": "2025-07-01", "total_amount": 10.0, "line_items": [{"name": "Test Item", "category": "Test", "amount": 10.0}]}'
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        # Create mock client structure
        mock_chat = MagicMock()
        mock_chat.completions = MagicMock()
        mock_chat.completions.create = MagicMock(return_value=mock_response)
        
        mock_client = MagicMock()
        mock_client.chat = mock_chat
        
        # Set up OpenAI client to return our mock client
        mock.OpenAI.return_value = mock_client
        
        yield mock

def test_openai_provider_initialization(mock_openai):
    provider = OpenAIProvider(api_key="fake-key", endpoint="fake-endpoint")
    mock_openai.OpenAI.assert_called_once_with(api_key="fake-key", base_url="fake-endpoint")
    assert provider.model_name == "gpt-3.5-turbo"

def test_openai_provider_send_request(mock_openai):
    provider = OpenAIProvider(api_key="fake-key", endpoint="fake-endpoint")
    result = provider.send_request("test-prompt")
    
    # Verify API call was made correctly
    mock_client = mock_openai.OpenAI.return_value
    mock_client.chat.completions.create.assert_called_once()
    
    # Check the call arguments
    args, kwargs = mock_client.chat.completions.create.call_args
    assert kwargs["model"] == "gpt-3.5-turbo"
    assert len(kwargs["messages"]) == 2
    assert kwargs["messages"][1]["content"] == "test-prompt"
    
    # Check the response
    assert result["provider"] == "openai"
    assert result["model"] == "gpt-3.5-turbo"
    assert "store_name" in result["response"]
    assert result["response"]["store_name"] == "Test Store"

def test_openai_provider_with_params(mock_openai):
    provider = OpenAIProvider(api_key="fake-key", endpoint="fake-endpoint")
    params = {"model": "gpt-4", "temperature": 0.1, "max_tokens": 1000}
    result = provider.send_request("test-prompt", params)
    
    # Check if model was updated
    assert result["model"] == "gpt-4"
    
    # Verify API call parameters
    args, kwargs = mock_openai.OpenAI.return_value.chat.completions.create.call_args
    assert kwargs["model"] == "gpt-4"
    assert kwargs["temperature"] == 0.1
    assert kwargs["max_tokens"] == 1000

def test_openai_provider_json_extraction(mock_openai):
    # Test with non-JSON response that contains markdown code blocks
    markdown_response = "```json\n{\"key\": \"value\"}\n```"
    mock_openai.OpenAI.return_value.chat.completions.create.return_value.choices[0].message.content = markdown_response
    
    provider = OpenAIProvider(api_key="fake-key", endpoint="fake-endpoint")
    result = provider.send_request("test-prompt")
    
    assert result["response"] == {"key": "value"}

def test_openai_provider_error_handling(mock_openai):
    # Test API error handling
    mock_openai.OpenAI.return_value.chat.completions.create.side_effect = RuntimeError("Rate limit exceeded")
    
    provider = OpenAIProvider(api_key="fake-key", endpoint="fake-endpoint")
    with pytest.raises(Exception) as excinfo:
        provider.send_request("test-prompt")
        
    # Just check that an exception was raised
    assert excinfo.value is not None

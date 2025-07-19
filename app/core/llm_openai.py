import logging
import json
import time
from typing import Any, Dict, Optional, List
from .llm_base import LLMProviderBase
import openai

class OpenAIProvider(LLMProviderBase):
    def __init__(self, api_key: str, endpoint: str):
        super().__init__(api_key, endpoint)
        self.client = openai.OpenAI(api_key=api_key, base_url=endpoint)
        self.model_name = "gpt-3.5-turbo"  # Default model
        self.default_params = {
            "temperature": 0.2,  # Low temperature for factual extraction
            "max_tokens": 2048,
            "response_format": {"type": "json_object"}  # Request JSON response
        }
    
    def send_request(self, prompt: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send request to OpenAI API and return parsed response."""
        logging.info(f"OpenAIProvider: Sending request to {self.endpoint}")
        
        start_time = time.time()
        
        try:
            # Prepare parameters, overriding defaults with any passed parameters
            request_params = self.default_params.copy()
            if params:
                if "model" in params:
                    self.model_name = params["model"]
                if "temperature" in params:
                    request_params["temperature"] = params["temperature"]
                if "max_tokens" in params:
                    request_params["max_tokens"] = params["max_tokens"]
            
            # Create the messages for the API call
            messages: List[Dict[str, str]] = [
                {"role": "system", "content": "You are an expert at parsing receipts. Provide output as valid JSON according to the schema."},
                {"role": "user", "content": prompt}
            ]
            
            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                **request_params
            )
            
            # Extract the content from the response
            if not response.choices or not response.choices[0].message.content:
                raise ValueError("Empty response from OpenAI API")
            
            response_text = response.choices[0].message.content
            
            # Parse the JSON response
            try:
                json_response = json.loads(response_text)
            except json.JSONDecodeError:
                # If JSON parsing fails, try extracting JSON from markdown blocks
                json_response = self._extract_json(response_text)
            
            elapsed_time = time.time() - start_time
            logging.info(f"OpenAIProvider: Request completed in {elapsed_time:.2f}s")
            
            return {
                "provider": "openai",
                "model": self.model_name,
                "response": json_response,
                "raw_response": response_text,
                "elapsed_time": elapsed_time
            }
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logging.error(f"OpenAIProvider: Error after {elapsed_time:.2f}s - {str(e)}")
            
            # Convert specific API exceptions to more generic ones for consistent error handling
            if "400" in str(e) or "invalid" in str(e).lower():
                raise ValueError(f"Invalid request to OpenAI API: {str(e)}")
            elif "429" in str(e) or "rate limit" in str(e).lower():
                raise openai.RateLimitError(f"Rate limit exceeded: {str(e)}")
            elif "500" in str(e) or "503" in str(e):
                raise openai.APIError(f"OpenAI service error: {str(e)}")
            else:
                raise
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text response, handling various response formats."""
        # Try to find JSON block in markdown formatted text
        json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
        import re
        json_match = re.search(json_pattern, text)
        
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # If extraction attempts fail, return the raw text
        return {"text": text}

import logging
import json
import time
from typing import Any, Dict, Optional
from .llm_base import LLMProviderBase
import google.generativeai as genai
import httpx

class GeminiProvider(LLMProviderBase):
    def __init__(self, api_key: str, endpoint: str):
        super().__init__(api_key, endpoint)
        genai.configure(api_key=api_key)
        self.model_name = "gemini-1.5-flash"  # Default model
        self.generation_config = {
            "temperature": 0.2,  # Low temperature for factual extraction
            "max_output_tokens": 2048,
            "response_mime_type": "application/json",
        }
    
    def send_request(self, prompt: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send request to Gemini API and return parsed response."""
        logging.info(f"GeminiProvider: Sending request to Gemini API using {self.model_name}")
        
        start_time = time.time()
        
        try:
            # Override default parameters if provided
            if params:
                if "model" in params:
                    self.model_name = params["model"]
                if "temperature" in params:
                    self.generation_config["temperature"] = params["temperature"]
                if "max_tokens" in params:
                    self.generation_config["max_output_tokens"] = params["max_tokens"]
            
            # Get the model
            model = genai.GenerativeModel(self.model_name)
            
            # Generate content
            response = model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            # Process the response
            if not response.candidates or not response.candidates[0].content.parts:
                raise ValueError("Empty response from Gemini API")
            
            response_text = response.candidates[0].content.parts[0].text
            
            # Extract JSON from the response if needed
            json_response = self._extract_json(response_text)
            
            elapsed_time = time.time() - start_time
            logging.info(f"GeminiProvider: Request completed in {elapsed_time:.2f}s")
            
            return {
                "provider": "gemini",
                "model": self.model_name,
                "response": json_response,
                "raw_response": response_text,
                "elapsed_time": elapsed_time
            }
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logging.error(f"GeminiProvider: Error after {elapsed_time:.2f}s - {str(e)}")
            
            # Convert specific API exceptions to more generic ones for consistent handling
            if "400" in str(e) or "invalid" in str(e).lower():
                raise ValueError(f"Invalid request to Gemini API: {str(e)}")
            elif "429" in str(e) or "rate limit" in str(e).lower():
                raise httpx.HTTPStatusError(f"Rate limit exceeded: {str(e)}", request=None, response=None)
            elif "500" in str(e) or "503" in str(e):
                raise httpx.HTTPStatusError(f"Gemini service error: {str(e)}", request=None, response=None)
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
        
        # Try parsing the entire text as JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # If all extraction attempts fail, return the raw text
        return {"text": text}

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class LLMProviderBase(ABC):
    def __init__(self, api_key: str, endpoint: str):
        self.api_key = api_key
        self.endpoint = endpoint

    @abstractmethod
    def send_request(self, prompt: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        pass

from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

# Define generic type for response data
T = TypeVar('T')

class BaseSchema(BaseModel):
    """
    Base schema with common configuration for all Pydantic models
    """
    class Config:
        from_attributes = True  # Allows conversion from ORM models
        populate_by_name = True

class ResponseBase(BaseModel, Generic[T]):
    """
    Base class for all API responses
    """
    status: str = "success"
    message: Optional[str] = None
    data: Optional[T] = None

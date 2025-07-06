from pydantic import BaseModel

class BaseSchema(BaseModel):
    """
    Base schema with common configuration for all Pydantic models
    """
    class Config:
        from_attributes = True  # Allows conversion from ORM models
        populate_by_name = True

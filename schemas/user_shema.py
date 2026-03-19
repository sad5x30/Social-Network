from pydantic import BaseModel, EmailStr
from datetime import datetime

class Users_schemas(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime
    is_active: bool
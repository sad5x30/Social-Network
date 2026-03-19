from pydantic import BaseModel
from datetime import datetime

class PostsCreate(BaseModel):
    content: str

class PostUpdate(BaseModel):
    content: str

class PostOut(BaseModel):
    id: int
    content: str
    created_at: datetime
    user_id: int
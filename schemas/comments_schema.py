from pydantic import BaseModel
from datetime import datetime

class CommentsSchemas(BaseModel):
    id: int
    user_id: int
    post_id: int
    content: str
    created_at: datetime
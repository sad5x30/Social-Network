from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse

from sqlalchemy.ext.asyncio import AsyncSession

from services.auth import get_current_user

from models.users import TableUsers
from models.posts import TablePosts
from database import async_session

router = APIRouter()

async def get_db():
    async with async_session() as db:
        yield db


@router.post("/create")
async def create_post(
    content: str = Form(...),
    session: AsyncSession = Depends(get_db),
    current_user: TableUsers = Depends(get_current_user),
):
    creating_post = TablePosts(
        content=content,
        user_id=current_user.id
    )

    session.add(creating_post)
    await session.commit()
    return RedirectResponse(url="/", status_code=303)

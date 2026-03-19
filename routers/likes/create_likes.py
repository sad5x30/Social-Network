from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session
from models.likes import TableLikes
from models.posts import TablePosts
from models.users import TableUsers
from services.auth import get_current_user

router = APIRouter()

async def get_db():
    async with async_session() as db:
        yield db

@router.post("/likes/{post_id}")
async def create_like(
    post_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TableUsers = Depends(get_current_user),
):
    post_exists = await session.execute(select(TablePosts.id).where(TablePosts.id == post_id))
    if post_exists.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    existing = await session.execute(
        select(TableLikes).where(
            TableLikes.post_id == post_id,
            TableLikes.user_id == current_user.id
        )
    )
    if existing.scalar_one_or_none():
        return RedirectResponse(url="/", status_code=303)

    session.add(TableLikes(user_id=current_user.id, post_id=post_id))
    await session.commit()
    return RedirectResponse(url="/", status_code=303)

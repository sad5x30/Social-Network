from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session
from models.posts import TablePosts
from models.users import TableUsers
from services.auth import get_current_user

router = APIRouter()

async def get_db():
    async with async_session() as db:
        yield db


@router.post("/update_post/{post_id}")
async def update_post(
    post_id: int,
    content: str = Form(...),
    session: AsyncSession = Depends(get_db),
    current_user: TableUsers = Depends(get_current_user)
):
    result = await session.execute(
        select(TablePosts)
        .where(TablePosts.id == post_id)
    )

    found_post = result.scalar_one_or_none()


    if not found_post:
        raise HTTPException(    
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )
    
    if found_post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не можете изменить не свой пост !"
        )
    
    found_post.content = content

    await session.commit()
    return RedirectResponse(url="/", status_code=303)

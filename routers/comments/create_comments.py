from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import RedirectResponse

from database import async_session

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth import get_current_user

from models.comments import TableComment
from models.posts import TablePosts
from models.users import TableUsers

router = APIRouter()


async def get_db():
    async with async_session() as db:
        yield db


@router.post("/create_comm")
async def create(
    post_id: int = Form(...),
    content: str = Form(...),
    session: AsyncSession = Depends(get_db),
    current_user: TableUsers = Depends(get_current_user),
):
    cleaned_content = content.strip()

    if not cleaned_content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid comment content.",
        )

    post_result = await session.execute(
        select(TablePosts.id).where(TablePosts.id == post_id)
    )
    post = post_result.scalar_one_or_none()
    
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found.",
        )

    creating_comment = TableComment(
        content=cleaned_content,
        user_id=current_user.id,
        post_id=post_id,
    )

    session.add(creating_comment)
    await session.commit()

    return RedirectResponse(url="/", status_code=303)

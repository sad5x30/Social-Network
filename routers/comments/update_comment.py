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


@router.patch("/update_comm/{post_id}/{comm_id}")
@router.post("/update_comm/{post_id}/{comm_id}")
async def update(
    post_id: int,
    comm_id: int,
    content: str = Form(...),
    session: AsyncSession = Depends(get_db),
    current_user: TableUsers = Depends(get_current_user),
):
    comment_result = await session.execute(
        select(TableComment).where(TableComment.id == comm_id)
    )
    comment = comment_result.scalar_one_or_none()
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found.",
        )

    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot update someone else's comment.",
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

    if comment.post_id != post_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment does not belong to this post.",
        )

    cleaned_content = content.strip()
    if not cleaned_content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid comment content.",
        )

    comment.content = cleaned_content
    await session.commit()

    return RedirectResponse(url="/", status_code=303)

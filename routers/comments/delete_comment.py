from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from database import async_session

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth import get_current_user

from models.comments import TableComment
from models.users import TableUsers

router = APIRouter()


async def get_db():
    async with async_session() as db:
        yield db


@router.delete("/delete_comm/{comm_id}")
@router.post("/delete_comm/{comm_id}")
async def deleting(
    comm_id: int,
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
            detail="You cannot delete someone else's comment.",
        )

    await session.delete(comment)
    await session.commit()

    return RedirectResponse(url="/", status_code=303)

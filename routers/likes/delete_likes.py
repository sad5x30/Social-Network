from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session
from models.likes import TableLikes
from models.users import TableUsers
from services.auth import get_current_user

router = APIRouter()

async def get_db():
    async with async_session() as db:
        yield db

@router.post("/likes/{post_id}/delete")
async def delete_like(
    post_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TableUsers = Depends(get_current_user),
):
    await session.execute(
        delete(TableLikes).where(
            TableLikes.post_id == post_id,
            TableLikes.user_id == current_user.id
        )
    )
    await session.commit()
    return RedirectResponse(url="/", status_code=303)

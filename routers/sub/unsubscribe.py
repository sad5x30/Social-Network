from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from database import async_session
from services.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
from models.users import TableUsers
from sqlalchemy import select
from models.subscriptions import TableSub

router = APIRouter()

async def get_db():
    async with async_session() as db:
        yield db

@router.post("/unsubscribe/{user_id}")
@router.delete("/unsubscribe/{user_id}")
async def unsubsribe(
    request: Request,
    user_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TableUsers = Depends(get_current_user),
):
    redirect_url = request.headers.get("referer") or "/"

    target_user = await session.execute(
        select(TableUsers.id).where(TableUsers.id == user_id)
    )
    target_user_id = target_user.scalar_one_or_none()

    if target_user_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    sub_result = await session.execute(
        select(TableSub).where(
            TableSub.user == current_user.id,
            TableSub.sub_user == target_user_id,
        )
    )
    sub_obj = sub_result.scalar_one_or_none()

    if sub_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    await session.delete(sub_obj)

    await session.commit()

    return RedirectResponse(url=redirect_url, status_code=303)

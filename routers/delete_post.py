from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import async_session
from models.posts import TablePosts
from models.users import TableUsers
from services.auth import get_current_user
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse

router = APIRouter()


async def get_db():
    async with async_session() as db:
        yield db


@router.delete("/delete/{post_id}")
@router.post("/delete/{post_id}")
async def deleting(
    post_id: int,
    request: Request,
    session: AsyncSession = Depends(get_db),
    current_user: TableUsers = Depends(get_current_user),
):
    result = await session.execute(
        select(TablePosts).where(TablePosts.id == post_id)
    )

    del_post = result.scalar_one_or_none()
    
    if not del_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )
    
    if del_post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы не можете удалить не свой пост !"
        )

    await session.delete(del_post)
    await session.commit()
    if request.method == "DELETE":
        return JSONResponse({"ok": True})

    return RedirectResponse(url="/", status_code=303)

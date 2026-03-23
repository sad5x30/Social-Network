from fastapi import APIRouter, Depends, Request, HTTPException, status, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from services.auth import get_current_user
from database import async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models.users import TableUsers
from models.chat import TableChats
from models.messages import TableMessages
from services.websocket_manager import send_message

router = APIRouter()
templates = Jinja2Templates(directory="templates")


async def get_db():
    async with async_session() as db:
        yield db


@router.post("/chat/{user_id}", response_class=HTMLResponse)
async def create_chat(
    request: Request,
    user_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TableUsers = Depends(get_current_user),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot create chat with yourself")

    u1, u2 = sorted((current_user.id, user_id))

    existing = await session.execute(
        select(TableChats).where(
            TableChats.user1_id == u1,
            TableChats.user2_id == u2,
        )
    )
    chat = existing.scalar_one_or_none()
    if chat:
        return RedirectResponse(url=f"/chat/{chat.id}", status_code=303)

    chat = TableChats(user1_id=u1, user2_id=u2)
    session.add(chat)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        existing = await session.execute(
            select(TableChats).where(
                TableChats.user1_id == u1,
                TableChats.user2_id == u2,
            )
        )
        chat = existing.scalar_one_or_none()

    if chat is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Chat creation failed")

    return RedirectResponse(url=f"/chat/{chat.id}", status_code=303)


@router.get("/chat/{chat_id}", response_class=HTMLResponse)
async def open_chat(
    request: Request,
    chat_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: TableUsers = Depends(get_current_user),
):
    chat_q = await session.execute(select(TableChats).where(TableChats.id == chat_id))
    chat = chat_q.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    if current_user.id not in (chat.user1_id, chat.user2_id):
        raise HTTPException(status_code=403, detail="Access denied")

    messages_q = await session.execute(
        select(TableMessages)
        .where(TableMessages.chat_id == chat_id)
        .options(selectinload(TableMessages.user))
        .order_by(TableMessages.created_at.asc())
    )
    new_message = messages_q.scalars().all()

    return templates.TemplateResponse(
        "chat/chat.html",
        {
            "request": request,
            "chat": chat,
            "new_message": new_message,
            "current_user_id": current_user.id,
        },
    )

@router.post("/message/{chat_id}")
async def message(chat_id: int, content: str = Form(...), session: AsyncSession = Depends(get_db), current_user: TableUsers = Depends(get_current_user)):
    text = content.strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Empty message")

    chat_q = await session.execute(select(TableChats).where(TableChats.id == chat_id))
    chat = chat_q.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    if current_user.id not in (chat.user1_id, chat.user2_id):
        raise HTTPException(status_code=403, detail="Access denied")

    new_message = TableMessages(chat_id=chat_id, sender_id=current_user.id, text=text)
    session.add(new_message)
    await session.commit()

    # определить получателя
    receiver_id = chat.user1_id if chat.user2_id == current_user.id else chat.user2_id

    await send_message(receiver_id, {
        "type": "new_message",
        "chat_id": chat_id,
        "text": text,
        "sender_id": current_user.id
    })

    return RedirectResponse(url=f"/chat/{chat_id}", status_code=303)

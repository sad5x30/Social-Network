from fastapi import FastAPI, Request, Depends, HTTPException, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from typing import AsyncGenerator

import models  # noqa: F401
from database import async_session
from models.posts import TablePosts
from models.comments import TableComment
from models.likes import TableLikes
from models.subscriptions import TableSub

from services.auth import router as auth_router
from services.auth import get_current_user_optional

from routers.create_post import router as create_router
from routers.delete_post import router as deleting_router
from routers.comments.create_comments import router as comments_router
from routers.comments.delete_comment import router as delete_comment_router
from routers.comments.update_comment import router as update_comment_router
from routers.update_post import router as update_router
from routers.likes.create_likes import router as likes_router
from routers.likes.delete_likes import router as likes_deleting_router
from routers.sub.subscibe import router as sub_router
from routers.sub.unsubscribe import router as unsub_router
from routers.chat.create_chat import router as chat_router

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(create_router)
app.include_router(deleting_router)
app.include_router(comments_router)
app.include_router(delete_comment_router)
app.include_router(update_comment_router)
app.include_router(update_router)
app.include_router(likes_router)
app.include_router(likes_deleting_router)
app.include_router(sub_router)
app.include_router(unsub_router)
app.include_router(chat_router)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

async def get_db():
    async with async_session() as db:
        yield db

@app.get('/', response_class=HTMLResponse)
async def Home(
    request: Request,
    limit: int = 10,
    offset: int = 0,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    posts = await session.execute(
        select(TablePosts).options(
            selectinload(TablePosts.user),
            selectinload(TablePosts.rel_comments).selectinload(TableComment.rel_comm_user),
            selectinload(TablePosts.rel_like),
        )
        .order_by(TablePosts.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = posts.scalars().all()

    liked_post_ids = set()
    subscribed_user_ids = set()
    if current_user:
        liked_posts_query = await session.execute(
            select(TableLikes.post_id).where(TableLikes.user_id == current_user.id)
        )
        liked_post_ids = set(liked_posts_query.scalars().all())
        subscribed_users_query = await session.execute(
            select(TableSub.sub_user).where(TableSub.user == current_user.id)
        )

        subscribed_user_ids = set(subscribed_users_query.scalars().all())

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "posts": result,
            "limit": limit,
            "offset": offset,
            "current_user_id": current_user.id if current_user else None,
            "liked_post_ids": liked_post_ids,
            "subscribed_user_ids": subscribed_user_ids,
        },
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


@app.get("/subscibes", response_class=HTMLResponse)
@app.get("/subscriptions", response_class=HTMLResponse)
async def subscriptions_page(
    request: Request,
    q: str = "",
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    if current_user is None:
        return templates.TemplateResponse(
            "subscibes.html",
            {
                "request": request,
                "subscriptions": [],
                "query": q,
                "total_count": 0,
                "mutual_count": 0,
                "is_authorized": False,
            },
        )

    subscriptions_query = await session.execute(
        select(TableSub)
        .options(selectinload(TableSub.rel_target_user))
        .where(TableSub.user == current_user.id)
        .order_by(TableSub.id.desc())
    )
    raw_subscriptions = subscriptions_query.scalars().all()

    followers_query = await session.execute(
        select(TableSub.user).where(TableSub.sub_user == current_user.id)
    )
    follower_ids = set(followers_query.scalars().all())

    subscribers_query = await session.execute(
        select(TableSub)
        .options(selectinload(TableSub.rel_subscribing_user))
        .where(TableSub.sub_user == current_user.id)
        .order_by(TableSub.id.desc())
    )
    raw_subscribers = subscribers_query.scalars().all()

    query = q.strip().lower()
    subscriptions = []
    for subscription in raw_subscriptions:
        target_user = subscription.rel_target_user
        if target_user is None:
            continue
        if query and query not in target_user.username.lower():
            continue

        subscriptions.append(
            {
                "id": target_user.id,
                "username": target_user.username,
                "initial": target_user.username[:1].upper(),
                "is_mutual": target_user.id in follower_ids,
                "avatar": target_user.avatar
            }
        )

    subscribers = []
    for subscription in raw_subscribers:
        subscriber_user = subscription.rel_subscribing_user
        if subscriber_user is None:
            continue
        if query and query not in subscriber_user.username.lower():
            continue

        subscribers.append(
            {
                "id": subscriber_user.id,
                "username": subscriber_user.username,
                "initial": subscriber_user.username[:1].upper(),
                "is_mutual": subscriber_user.id in {item["id"] for item in subscriptions},
                "avatar": subscriber_user.avatar,
            }
        )

    subscribed_user_ids = {subscription.sub_user for subscription in raw_subscriptions}
    mutual_count = len(subscribed_user_ids.intersection(follower_ids))

    return templates.TemplateResponse(
        "subscibes.html",
        {
            "request": request,
            "subscriptions": subscriptions,
            "subscribers": subscribers,
            "query": q,
            "total_count": len(raw_subscriptions),
            "subscribers_count": len(raw_subscribers),
            "mutual_count": mutual_count,
            "is_authorized": True,
        },
    )

async def universal_error_handler(request: Request, exc: Exception):
    status_code = getattr(exc, "status_code", 500)
    detail = getattr(exc, "detail", str(exc) or "Internal Server Error")

    return templates.TemplateResponse(
        "errors/error_page.html",  # один файл для всех ошибок
        {
            "request": request,
            "status_code": status_code,
            "detail": detail,  # сообщение ошибки
        },
        status_code=status_code,
    )

# Регистрируем обработчик для нужных ошибок
for code in [404, 500, 403, 401, 405]:
    app.exception_handlers[code] = universal_error_handler

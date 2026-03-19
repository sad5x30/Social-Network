from fastapi import Depends, HTTPException, APIRouter, Request, Form, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from database import async_session
from models.users import TableUsers
from sqlalchemy import select
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
import os
import hashlib
import bcrypt
from pathlib import Path
from dotenv import load_dotenv
import aiofiles

router = APIRouter()
templates = Jinja2Templates(directory="templates")

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env.txt")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

UPLOAD_DIR = "static/avatars"
os.makedirs(UPLOAD_DIR, exist_ok=True)

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set")

async def get_db():
    async with async_session() as db:
        yield db


def _password_to_bcrypt_input(password: str) -> bytes:
    # Pre-hash removes bcrypt 72-byte input limit while keeping bcrypt as KDF.
    return hashlib.sha256(password.encode("utf-8")).hexdigest().encode("ascii")


def hash_password(password: str):
    normalized = _password_to_bcrypt_input(password)
    return bcrypt.hashpw(normalized, bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password, hashed_password):
    hashed_bytes = hashed_password.encode("utf-8")

    # Backward compatibility for previously stored raw bcrypt hashes.
    try:
        if bcrypt.checkpw(plain_password.encode("utf-8"), hashed_bytes):
            return True
    except ValueError:
        pass

    normalized = _password_to_bcrypt_input(plain_password)
    return bcrypt.checkpw(normalized, hashed_bytes)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.get("/login", response_class=HTMLResponse)
async def login_page(request:Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TableUsers).where(TableUsers.username == form_data.username)
    )

    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Not found")
    
    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="wrong password")
    
    access_token = create_access_token({"sub": str(user.id)})

    redirect = RedirectResponse("/", status_code=303)
    redirect.set_cookie(key="access_token", value=access_token, httponly=True)
    return redirect

@router.get("/register", response_class=HTMLResponse)
async def register_page(request:Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})

@router.post("/register")
async def register(username: str = Form(), password: str = Form(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TableUsers).where(TableUsers.username == username)
    )

    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    hashed_pw = hash_password(password)

    new_user = TableUsers(
        username = username,
        password = hashed_pw
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return RedirectResponse("/auth/login", status_code=303)


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(
        select(TableUsers).where(TableUsers.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        return None

    result = await db.execute(
        select(TableUsers).where(TableUsers.id == user_id)
    )
    return result.scalar_one_or_none()

@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, current_user: TableUsers = Depends(get_current_user)):
    return templates.TemplateResponse(
        "auth/profile.html",
        {
            "request":request,
            "current_user":current_user
        }
    )

@router.post("/users/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: TableUsers = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File is required")

    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Only JPEG or PNG files are allowed")

    extension = Path(file.filename).suffix.lower() or ".jpg"
    file_name = f"user_{current_user.id}{extension}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    current_user.avatar = f"/{file_path.replace(os.sep, '/')}"
    await session.commit()

    return RedirectResponse(url="/auth/profile", status_code=303)

@router.get("/logout")
async def logout():
    response = RedirectResponse("/auth/login", status_code=303)
    response.delete_cookie("access_token")
    return response

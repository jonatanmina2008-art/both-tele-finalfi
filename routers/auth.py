from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.database import get_db
from models.orm import Account
from pydantic import BaseModel, EmailStr
import bcrypt
from jose import jwt
from datetime import datetime, timedelta
import os

router = APIRouter(prefix="/auth", tags=["Authentication"])

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-shopthalex-key-12345")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    # Check if account already exists
    result = await db.execute(select(Account).filter(Account.email == user_data.email))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    # Hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(user_data.password.encode('utf-8'), salt).decode('utf-8')

    # Create account
    new_account = Account(
        email=user_data.email,
        password_hash=hashed,
        name=user_data.name,
        role="client", # Default role for new signups
        is_active=True
    )
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)

    # Generate token
    token_data = {"sub": str(new_account.id), "role": new_account.role}
    token = create_access_token(token_data)
    
    return {"access_token": token, "token_type": "bearer", "role": new_account.role}

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Account).filter(Account.email == credentials.email))
    account = result.scalars().first()
    if not account or account.is_suspended:
        raise HTTPException(status_code=401, detail="Credenciales inválidas o cuenta suspendida")

    if not bcrypt.checkpw(credentials.password.encode('utf-8'), account.password_hash.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token_data = {"sub": str(account.id), "role": account.role}
    token = create_access_token(token_data)

    return {"access_token": token, "token_type": "bearer", "role": account.role}

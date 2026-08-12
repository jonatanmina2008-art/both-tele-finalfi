from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.database import get_db
from models.orm import Account
from pydantic import BaseModel, EmailStr
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import bcrypt
import os

router = APIRouter(prefix="/accounts", tags=["Account Management"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

SECRET_KEY = os.getenv("JWT_SECRET", "super-secret-shopthalex-key-12345")
ALGORITHM = "HS256"

class AccountCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str # 'reseller' or 'client'

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> Account:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token no válido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token no válido")
        
    result = await db.execute(select(Account).filter(Account.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_account_by_parent(
    data: AccountCreate, 
    current_user: Account = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    """
    Super Admin can create Resellers and Clients.
    Resellers can only create Clients (their sub-clients).
    """
    # Permission validations
    if current_user.role == 'client':
        raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")
        
    if current_user.role == 'reseller' and data.role != 'client':
        raise HTTPException(status_code=403, detail="Los revendedores solo pueden crear cuentas de clientes")

    # Check if duplicate email
    result = await db.execute(select(Account).filter(Account.email == data.email))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(data.password.encode('utf-8'), salt).decode('utf-8')

    new_account = Account(
        email=data.email,
        password_hash=hashed,
        name=data.name,
        role=data.role,
        created_by=current_user.id,
        is_active=True
    )
    db.add(new_account)
    await db.commit()
    return {"message": "Cuenta creada con éxito", "role": data.role}

@router.get("/my-clients")
async def list_my_clients(current_user: Account = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Returns clients created by this specific reseller or all accounts if superadmin.
    Shows the 'created_by' tag to prevent deleting someone else's client by mistake.
    """
    if current_user.role == 'superadmin':
        result = await db.execute(select(Account))
        accounts = result.scalars().all()
    elif current_user.role == 'reseller':
        result = await db.execute(select(Account).filter(Account.created_by == current_user.id))
        accounts = result.scalars().all()
    else:
        raise HTTPException(status_code=403, detail="No autorizado")

    return [
        {
            "id": acc.id,
            "email": acc.email,
            "name": acc.name,
            "role": acc.role,
            "is_suspended": acc.is_suspended,
            "created_by": acc.created_by,
            "owner_info": "Super Admin" if not acc.created_by else "Revendedor"
        }
        for acc in accounts
    ]

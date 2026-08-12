from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.database import get_db
from models.orm import Account
from services.email_imap import test_imap_connection
from services.email_parser import verify_payment_via_imap
from routers.accounts import get_current_user
from pydantic import BaseModel, EmailStr
import logging

router = APIRouter(prefix="/payments", tags=["Payment Verification"])
logger = logging.getLogger(__name__)

class TestIMAPRequest(BaseModel):
    host: str
    port: int = 993
    email: EmailStr
    app_password: str
    use_ssl: bool = True

class VerifyPaymentRequest(BaseModel):
    payment_type: str # 'binance' or 'bank'
    ref_or_txid: str
    amount: float

@router.post("/test-connection")
async def test_imap(data: TestIMAPRequest, current_user: Account = Depends(get_current_user)):
    """
    Tests if the provided email and App Password successfully connect to the IMAP server.
    """
    connected = await test_imap_connection(
        host=data.host,
        port=data.port,
        email_address=data.email,
        password=data.app_password,
        use_ssl=data.use_ssl
    )
    if not connected:
        raise HTTPException(
            status_code=400, 
            detail="No se pudo conectar al servidor de correo. Verifica el email y la Contraseña de Aplicación (App Password)."
        )
    return {"message": "Conexión IMAP probada con éxito"}

@router.post("/verify")
async def verify_payment(
    data: VerifyPaymentRequest, 
    current_user: Account = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Simulates email fetching to verify a transaction amount and TXID / Reference.
    """
    # For testing, we verify via a mockup if parameters are missing,
    # otherwise we call the real IMAP verification service.
    # Replace the parameters below with the configured IMAP info from payment_configs table.
    # E.g., select payment_configs where account_id = current_user.id
    
    # Placeholder credentials test
    imap_host = "imap.gmail.com"
    email_user = current_user.email
    # App passwords should be fetched decrypted from DB
    decrypted_password = "dummypassword" 

    verified = await verify_payment_via_imap(
        host=imap_host,
        port=993,
        email_addr=email_user,
        password=decrypted_password,
        payment_type=data.payment_type,
        ref_or_txid=data.ref_or_txid,
        amount=data.amount
    )
    
    return {"verified": verified}

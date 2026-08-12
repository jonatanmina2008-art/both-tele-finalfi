import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    _key = Fernet.generate_key()
    ENCRYPTION_KEY = _key.decode()

fernet = Fernet(ENCRYPTION_KEY.encode())

def encrypt_password(password: str) -> str:
    """Encrypts a plaintext password."""
    if not password:
        return ""
    return fernet.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password: str) -> str:
    """Decrypts an encrypted password."""
    if not encrypted_password:
        return ""
    try:
        return fernet.decrypt(encrypted_password.encode()).decode()
    except Exception as e:
        raise ValueError("Failed to decrypt password") from e

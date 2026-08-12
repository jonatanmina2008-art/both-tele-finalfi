import imaplib
import logging
import asyncio

logger = logging.getLogger(__name__)

async def test_imap_connection(host: str, port: int, email_address: str, password: str, use_ssl: bool = True) -> bool:
    """
    Tests IMAP connection for universal email validation (e.g., Binance, Bank).
    """
    def _connect():
        try:
            if use_ssl:
                mail = imaplib.IMAP4_SSL(host, port)
            else:
                mail = imaplib.IMAP4(host, port)
            
            mail.login(email_address, password)
            mail.logout()
            return True
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP login failed for {email_address}: {e}")
            return False
        except Exception as e:
            logger.error(f"IMAP connection error for {host}:{port}: {e}")
            return False

    return await asyncio.to_thread(_connect)

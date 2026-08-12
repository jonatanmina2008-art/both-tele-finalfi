import imaplib
import email
from email.header import decode_header
import re
import logging
import asyncio

logger = logging.getLogger(__name__)

def parse_email_for_binance(body: str, txid: str, expected_amount: float) -> bool:
    """
    Parses email body looking for Binance Pay confirmation of txid and amount.
    """
    # Normalize text
    body_clean = body.replace("\r", "").replace("\n", " ")
    
    # Search for TXID in body
    if txid not in body_clean:
        return False
        
    # Regex to find transaction amounts (e.g. 10.50, $10.50, 10,50 USD, etc.)
    amount_patterns = [
        r"(?:usd|usdt|\$)\s*([\d\.,]+)", 
        r"([\d\.,]+)\s*(?:usd|usdt)"
    ]
    
    for pattern in amount_patterns:
        matches = re.findall(pattern, body_clean, re.IGNORECASE)
        for match in matches:
            try:
                # Standardize float format (replace comma with dot if necessary)
                val = float(match.replace(",", "."))
                if abs(val - expected_amount) < 0.01:
                    return True
            except ValueError:
                continue
    return False

def parse_email_for_bank(body: str, reference: str, expected_amount: float) -> bool:
    """
    Parses email body looking for Ecuadorian Bank (Pichincha, etc.) transfer confirmation.
    """
    body_clean = body.replace("\r", "").replace("\n", " ")
    
    # Search for transfer reference code
    if reference not in body_clean:
        return False
        
    # Search for amount matching
    amount_patterns = [
        r"(?:usd|val|monto|\$)\s*([\d\.,]+)",
        r"([\d\.,]+)\s*(?:usd|dolares|dólares)"
    ]
    
    for pattern in amount_patterns:
        matches = re.findall(pattern, body_clean, re.IGNORECASE)
        for match in matches:
            try:
                val = float(match.replace(",", "."))
                if abs(val - expected_amount) < 0.01:
                    return True
            except ValueError:
                continue
    return False

async def verify_payment_via_imap(
    host: str, 
    port: int, 
    email_addr: str, 
    password: str, 
    payment_type: str, 
    ref_or_txid: str, 
    amount: float
) -> bool:
    """
    Asynchronously logs into IMAP, fetches latest emails, and verifies Binance/Bank confirmations.
    """
    def _fetch_and_verify():
        try:
            mail = imaplib.IMAP4_SSL(host, port)
            mail.login(email_addr, password)
            mail.select("INBOX")
            
            # Filter from typical transaction notification emails
            if payment_type == "binance":
                # Binance Pay notification emails usually from: do-not-reply@directmail.binance.com or similar
                status, messages = mail.search(None, '(FROM "binance.com")')
            else:
                # Banks in Ecuador like Pichincha notify from: transferencias@pichincha.com / bancamovil@pichincha.com
                status, messages = mail.search(None, 'ALL')
                
            if status != "OK":
                mail.logout()
                return False
                
            email_ids = messages[0].split()
            # Check the 10 most recent emails
            for e_id in reversed(email_ids[-10:]):
                res, data = mail.fetch(e_id, "(RFC822)")
                if res != "OK":
                    continue
                    
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Extract text body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type in ["text/plain", "text/html"]:
                            try:
                                body += part.get_payload(decode=True).decode(errors="ignore")
                            except Exception:
                                pass
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")
                    
                # Verify based on payment method
                if payment_type == "binance":
                    if parse_email_for_binance(body, ref_or_txid, amount):
                        mail.logout()
                        return True
                else:
                    if parse_email_for_bank(body, ref_or_txid, amount):
                        mail.logout()
                        return True
                        
            mail.logout()
            return False
        except Exception as e:
            logger.error(f"Error checking IMAP emails: {e}")
            return False

    return await asyncio.to_thread(_fetch_and_verify)

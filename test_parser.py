import asyncio
from services.email_parser import parse_email_for_binance, parse_email_for_bank

async def test_email_verification():
    print("Iniciando pruebas del parseador de emails...")

    # Mock de cuerpo de correo de Binance Pay
    binance_email = """
    Binance Pay Notification:
    You have received a payment of 10.50 USD.
    Transaction ID (TXID): 987654321
    Status: Completed.
    """

    # Mock de cuerpo de correo de transferencia bancaria de Pichincha
    bank_email = """
    Notificacion de Transferencia:
    Se ha realizado una transferencia a su cuenta de ahorros.
    Monto recibido: $15.75 USD.
    Numero de referencia: REF-44332211
    """

    # Prueba 1: Verificar Binance con TXID y monto correcto
    res_binance_ok = parse_email_for_binance(binance_email, "987654321", 10.50)
    print(f"Prueba 1 (Binance Exitoso): {'PASO' if res_binance_ok else 'FALLO'}")

    # Prueba 2: Verificar Binance con monto incorrecto
    res_binance_wrong_amount = parse_email_for_binance(binance_email, "987654321", 9.99)
    print(f"Prueba 2 (Binance Monto Incorrecto): {'PASO (Detecto error)' if not res_binance_wrong_amount else 'FALLO'}")

    # Prueba 3: Verificar Banco con referencia y monto correcto
    res_bank_ok = parse_email_for_bank(bank_email, "REF-44332211", 15.75)
    print(f"Prueba 3 (Banco Pichincha Exitoso): {'PASO' if res_bank_ok else 'FALLO'}")

    # Prueba 4: Verificar Banco con referencia incorrecta
    res_bank_wrong_ref = parse_email_for_bank(bank_email, "REF-00000000", 15.75)
    print(f"Prueba 4 (Banco Referencia Incorrecta): {'PASO (Detecto error)' if not res_bank_wrong_ref else 'FALLO'}")

if __name__ == "__main__":
    asyncio.run(test_email_verification())

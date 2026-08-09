from ps_manager.services.crypto_vault_service import CryptoVaultService
from ps_manager.services.db_service import DatabaseService
from ps_manager.services.log_buffer_service import LogBufferService

def test_crypto_service():
    master_key = "ChaveSecretaPM"
    data = b"Credencial secreta"
    enc = CryptoVaultService.encrypt(data, master_key)
    dec = CryptoVaultService.decrypt(enc, master_key)
    assert dec == data

def test_password_strength():
    res = CryptoVaultService.evaluate_password_strength("MinhaS3nhaS3gura!2026")
    assert res["strength"] in ("Forte", "Excelente")

def test_db_service():
    db = DatabaseService(":memory:")
    assert db.set_key("pm_theme", "corporate") is True
    assert db.get_key("pm_theme") == "corporate"

def test_log_buffer_service():
    log_buffer = LogBufferService(max_entries=10)
    log_buffer.info("Cofre acessado", source="ps_manager")
    logs = log_buffer.get_logs()
    assert len(logs) == 1
    assert logs[0]["message"] == "Cofre acessado"

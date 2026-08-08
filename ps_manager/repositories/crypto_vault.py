import os
import base64
import hashlib
import json
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from ps_manager.domain.entities import Credential, VaultData
from ps_manager.repositories.base import AbstractVaultRepository

SALT_PREFIX = b"SALT_PBKDF2_V1:"
SALT_LEN = 16
PBKDF2_ITERATIONS = 600_000

class CryptoVaultRepository(AbstractVaultRepository):
    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path

    @staticmethod
    def derive_key_pbkdf2(master_key: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
        )
        return base64.urlsafe_b64encode(kdf.derive(master_key.encode('utf-8')))

    @staticmethod
    def _legacy_derive_key(master_key: str) -> bytes:
        digest = hashlib.sha256(master_key.encode('utf-8')).digest()
        return base64.urlsafe_b64encode(digest)

    def vault_exists(self) -> bool:
        return self.storage_path.exists() and self.storage_path.stat().st_size > 0

    def load_vault(self, master_key: str) -> VaultData:
        if not self.vault_exists():
            return VaultData(version=1, senhas=[])

        raw_encrypted = self.storage_path.read_bytes()

        # Checar se usa PBKDF2 (com prefixo e salt)
        if raw_encrypted.startswith(SALT_PREFIX):
            salt_start = len(SALT_PREFIX)
            salt = raw_encrypted[salt_start : salt_start + SALT_LEN]
            payload = raw_encrypted[salt_start + SALT_LEN :]
            try:
                fernet_key = self.derive_key_pbkdf2(master_key, salt)
                f = Fernet(fernet_key)
                decrypted = f.decrypt(payload)
                data = json.loads(decrypted.decode('utf-8'))
                senhas = [Credential.from_dict(c) for c in data.get("senhas", [])]
                return VaultData(version=data.get("version", 1), senhas=senhas)
            except InvalidToken as e:
                raise PermissionError("Chave Mestre incorreta ou cofre corrompido.") from e

        # Fallback para cofre legado (Fernet direta ou SHA-256 simples) e upgrade automático
        decrypted = None
        try:
            f_direct = Fernet(master_key.encode('utf-8'))
            decrypted = f_direct.decrypt(raw_encrypted)
        except Exception:
            pass

        if decrypted is None:
            try:
                legacy_key = self._legacy_derive_key(master_key)
                f_legacy = Fernet(legacy_key)
                decrypted = f_legacy.decrypt(raw_encrypted)
            except Exception as e:
                raise PermissionError("Chave Mestre incorreta ou cofre corrompido.") from e

        data = json.loads(decrypted.decode('utf-8'))
        senhas = [Credential.from_dict(c) for c in data.get("senhas", [])]
        vault = VaultData(version=data.get("version", 1), senhas=senhas)
        
        # Migrar automaticamente para PBKDF2 + Salt
        self.save_vault(vault, master_key)
        return vault

    def save_vault(self, vault: VaultData, master_key: str) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.storage_path.parent, 0o700)
        except Exception:
            pass

        salt = os.urandom(SALT_LEN)
        fernet_key = self.derive_key_pbkdf2(master_key, salt)
        f = Fernet(fernet_key)

        data = {
            "version": vault.version,
            "senhas": [c.to_dict() for c in vault.senhas]
        }
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        encrypted_payload = f.encrypt(json_str.encode('utf-8'))
        full_bytes = SALT_PREFIX + salt + encrypted_payload
        
        self.storage_path.write_bytes(full_bytes)
        try:
            os.chmod(self.storage_path, 0o600)
        except Exception:
            pass

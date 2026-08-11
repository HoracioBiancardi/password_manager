from __future__ import annotations
from functools import lru_cache
from password_manager.config import get_settings
from password_manager.repositories.crypto_vault import CryptoVaultRepository
from password_manager.services.vault_service import VaultService

@lru_cache
def _get_repository() -> CryptoVaultRepository:
    settings = get_settings()
    return CryptoVaultRepository(settings.storage_path)

def get_vault_service() -> VaultService:
    return VaultService(_get_repository())

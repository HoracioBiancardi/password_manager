from __future__ import annotations
from abc import ABC, abstractmethod
from password_manager.domain.entities import Credential, VaultData

class AbstractVaultRepository(ABC):
    @abstractmethod
    def load_vault(self, master_key: str) -> VaultData: ...

    @abstractmethod
    def save_vault(self, vault: VaultData, master_key: str) -> None: ...

    @abstractmethod
    def vault_exists(self) -> bool: ...

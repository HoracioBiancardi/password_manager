"""Dependências injetáveis do FastAPI."""

from fastapi import Header, HTTPException

from password_manager.config import Settings
from password_manager.crypto.crypto_service import CryptoService
from password_manager.exceptions import ChaveMestreInvalidaError
from password_manager.services.notas_service import NotasService
from password_manager.services.password_manager_service import PasswordManagerService
from password_manager.storage.file_storage import FileStorage


def get_notas_servico(
    x_master_key: str = Header(..., description="Chave Mestre Fernet"),
) -> NotasService:
    settings = Settings()
    notas_path = settings.notas_path
    notas_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        return NotasService(
            crypto=CryptoService(x_master_key),
            storage=FileStorage(notas_path),
        )
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")


def get_servico(
    x_master_key: str = Header(..., description="Chave Mestre Fernet"),
) -> PasswordManagerService:
    """Dependência FastAPI que instancia o serviço com a chave do header.

    Args:
        x_master_key: Header X-Master-Key contendo a chave Fernet.

    Returns:
        PasswordManagerService configurado e pronto para uso.

    Raises:
        HTTPException: 401 se o formato da chave for inválido.
    """
    settings = Settings()
    storage_path = settings.storage_path
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        return PasswordManagerService(
            crypto=CryptoService(x_master_key),
            storage=FileStorage(storage_path),
        )
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")

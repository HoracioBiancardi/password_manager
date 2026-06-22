"""Configuração da aplicação via variáveis de ambiente e arquivo .env."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

CAMINHO_ENV: Path = Path(".password-manager") / ".env"
CAMINHO_STORAGE_PADRAO: Path = Path(".password-manager") / "senhas.enc"
CAMINHO_NOTAS_PADRAO: Path = Path(".password-manager") / "notas.enc"


class Settings(BaseSettings):
    """Configurações carregadas do .env ou variáveis de ambiente.

    Attributes:
        master_key: Chave mestre Fernet. Se definida, dispensa prompt interativo.
        storage_path: Caminho para o arquivo de senhas criptografadas.
    """

    model_config = SettingsConfigDict(
        env_file=str(CAMINHO_ENV),
        env_file_encoding="utf-8",
    )

    master_key: str | None = None
    storage_path: Path = CAMINHO_STORAGE_PADRAO
    notas_path: Path = CAMINHO_NOTAS_PADRAO

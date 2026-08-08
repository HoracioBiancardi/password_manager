from pathlib import Path

CAMINHO_STORAGE_PADRAO: Path = Path(".password-manager") / "senhas.enc"

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    class Settings(BaseSettings):
        storage_path: Path = CAMINHO_STORAGE_PADRAO
        host: str = "127.0.0.1"
        port: int = 8000
        debug: bool = False

        model_config = SettingsConfigDict(
            env_prefix="PM_",
            env_file=".env",
            env_file_encoding="utf-8",
        )

except ImportError:
    class Settings:
        storage_path: Path = CAMINHO_STORAGE_PADRAO
        host: str = "127.0.0.1"
        port: int = 8000
        debug: bool = False

settings = Settings()

def get_settings() -> Settings:
    return settings

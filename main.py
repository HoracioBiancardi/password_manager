"""
Entrypoint principal do Password Manager.
Re-exporta a aplicação FastAPI de password_manager.main para padronização de inicialização.
"""
from password_manager.main import app

__all__ = ["app"]

"""
Entrypoint principal do Password Manager.
Re-exporta a aplicação FastAPI de ps_manager.main para padronização de inicialização.
"""
from ps_manager.main import app

__all__ = ["app"]

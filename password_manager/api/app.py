"""Configuração e inicialização da aplicação FastAPI."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .routes import router
from .routes_io import router as router_io

_FRONTEND_DIR: Path = Path(__file__).parent.parent / "frontend"


def create_app() -> FastAPI:
    """Cria e configura a instância da aplicação FastAPI.

    Returns:
        Aplicação FastAPI com middlewares e rotas registradas.
    """
    app = FastAPI(
        title="Password Manager API",
        version="0.1.0",
        description="API local para gerenciamento de senhas criptografadas.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def frontend() -> HTMLResponse:
        """Serve a interface web de gestão de senhas."""
        return HTMLResponse((_FRONTEND_DIR / "index.html").read_text(encoding="utf-8"))

    @app.get("/health", tags=["sistema"])
    def health() -> dict[str, str]:
        """Verifica se a API está operacional."""
        return {"status": "ok"}

    app.include_router(router, prefix="/api")
    app.include_router(router_io, prefix="/api")

    app.mount("/static", StaticFiles(directory=str(_FRONTEND_DIR)), name="static")
    return app


app = create_app()


def start() -> None:
    """Ponto de entrada para iniciar o servidor via script pm-api."""
    import uvicorn

    uvicorn.run("password_manager.api.app:app", host="127.0.0.1", port=8080)

import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from password_manager.config import get_settings
from password_manager.routers import credentials, vault, settings as settings_router, system, vault_tools, tasks
from password_manager.services.log_buffer_service import log_buffer_service

def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(
        title="PS Manager V2",
        debug=s.debug,
        docs_url="/docs" if s.debug else None,
        redoc_url="/redoc" if s.debug else None,
        openapi_url="/openapi.json" if s.debug else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Captura logging padrão (logging.getLogger(__name__)) no buffer de logs da UI
    logging.getLogger().addHandler(log_buffer_service.get_handler())

    app.include_router(credentials.router)
    app.include_router(vault.router)
    app.include_router(settings_router.router)
    app.include_router(system.router)
    app.include_router(vault_tools.router)
    app.include_router(tasks.router)

    @app.get("/health")
    def health():
        return {"status": "ok", "app": "PS Manager V2"}

    frontend_dir = Path(__file__).resolve().parent / "frontend"
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def index():
        return FileResponse(frontend_dir / "index.html")

    return app

app = create_app()

def start():
    s = get_settings()
    uvicorn.run("password_manager.main:app", host=s.host, port=s.port, reload=s.debug)

if __name__ == "__main__":
    start()

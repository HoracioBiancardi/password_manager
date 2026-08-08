from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from ps_manager.config import get_settings
from ps_manager.routers import credentials, vault, settings as settings_router

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

    app.include_router(credentials.router)
    app.include_router(vault.router)
    app.include_router(settings_router.router)

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
    uvicorn.run("ps_manager.main:app", host=s.host, port=s.port, reload=s.debug)

if __name__ == "__main__":
    start()

"""Endpoints de exportação e importação de dados."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from password_manager.config import Settings
from password_manager.crypto.crypto_service import CryptoService
from password_manager.exceptions import ChaveMestreInvalidaError
from password_manager.models.credencial import Credencial
from password_manager.services.password_manager_service import PasswordManagerService

from .dependencies import get_servico

router = APIRouter(prefix="/io", tags=["import/export"])

_FORMAT_VERSION = 1


class ImportPayload(BaseModel):
    version: int = _FORMAT_VERSION
    senhas: list[dict] = []
    notas: list[dict] = []


@router.get("/export")
def exportar(
    servico: PasswordManagerService = Depends(get_servico),
) -> JSONResponse:
    """Exporta todas as senhas em formato JSON descriptografado."""
    try:
        senhas = [c.to_dict() for c in servico.listar_credenciais()]
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")

    payload = {
        "version": _FORMAT_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "senhas": senhas,
    }
    filename = f"pm-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/vault")
def reset_vault(x_master_key: str = Header(...)) -> dict[str, str]:
    """Apaga o cofre de senhas. Valida o formato da chave (sem descriptografar o vault)."""
    try:
        CryptoService(x_master_key)
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")
    settings = Settings()
    settings.storage_path.unlink(missing_ok=True)
    return {"detail": "Cofre apagado."}


@router.post("/import")
def importar(
    payload: ImportPayload,
    servico: PasswordManagerService = Depends(get_servico),
) -> dict:
    """Importa senhas, ignorando duplicatas já existentes."""
    try:
        senhas_existentes = servico.listar_credenciais()
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")

    chaves_senhas = {(c.nome, c.email) for c in senhas_existentes}
    senhas_importadas = 0

    try:
        for d in payload.senhas:
            cred = Credencial.from_dict(d)
            if (cred.nome, cred.email) not in chaves_senhas:
                servico.adicionar_credencial(cred)
                chaves_senhas.add((cred.nome, cred.email))
                senhas_importadas += 1
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"Arquivo inválido: {exc}")

    return {
        "senhas_importadas": senhas_importadas,
        "senhas_ignoradas": len(payload.senhas) - senhas_importadas,
    }

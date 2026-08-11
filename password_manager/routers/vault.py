from __future__ import annotations
import json
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import Response
from password_manager.config import get_settings
from password_manager.dependencies import get_vault_service
from password_manager.domain.entities import Credential, VaultData
from password_manager.models.schemas import (
    VaultExportResponse,
    VaultImportPayload,
    VaultImportResponse,
)
from password_manager.routers.credentials import get_master_key
from password_manager.services.vault_service import VaultService

router = APIRouter(tags=["cofre"])

# ── JSON Export / Import ───────────────────────────────────────────
@router.get("/api/cofre/exportar", response_model=VaultExportResponse)
@router.get("/api/io/export", response_model=VaultExportResponse)
def exportar_cofre(
    master_key: str = Depends(get_master_key),
    service: VaultService = Depends(get_vault_service),
) -> VaultExportResponse:
    try:
        vault = service.exportar_vault(master_key)
        return VaultExportResponse(
            version=vault.version,
            senhas=[c.to_dict() for c in vault.senhas]
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e

@router.post("/api/cofre/importar", response_model=VaultImportResponse)
@router.post("/api/io/import", response_model=VaultImportResponse)
def importar_cofre(
    body: VaultImportPayload,
    master_key: str = Depends(get_master_key),
    service: VaultService = Depends(get_vault_service),
) -> VaultImportResponse:
    try:
        raw_list = [c.model_dump() for c in body.senhas]
        res = service.importar_vault(master_key, raw_list)
        return VaultImportResponse(**res)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e

# ── Encrypted (.enc) Export / Import ────────────────────────────────
@router.get("/api/cofre/exportar-criptografado")
@router.get("/api/io/export-encrypted")
def exportar_criptografado(
    master_key: str = Depends(get_master_key),
) -> Response:
    settings = get_settings()
    if not settings.storage_path.exists():
        raise HTTPException(status_code=404, detail="Cofre ainda não foi criado.")
    
    content = settings.storage_path.read_bytes()
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=backup-senhas.enc"}
    )

@router.post("/api/cofre/importar-criptografado", response_model=VaultImportResponse)
@router.post("/api/io/import-encrypted", response_model=VaultImportResponse)
async def importar_criptografado(
    request: Request,
    master_key: str = Depends(get_master_key),
    service: VaultService = Depends(get_vault_service),
) -> VaultImportResponse:
    try:
        content = await request.body()
        if not content:
            raise HTTPException(status_code=400, detail="Arquivo criptografado vazio.")

        import os
        import tempfile
        from pathlib import Path
        from password_manager.repositories.crypto_vault import CryptoVaultRepository

        with tempfile.NamedTemporaryFile(suffix=".enc", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            os.chmod(tmp_path, 0o600)
            tmp.write(content)

        try:
            temp_repo = CryptoVaultRepository(tmp_path)
            imported_vault = temp_repo.load_vault(master_key)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

        raw_list = [c.to_dict() for c in imported_vault.senhas]
        res = service.importar_vault(master_key, raw_list)
        return VaultImportResponse(**res)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Erro ao importar backup: {e}") from e

from fastapi import Query

@router.delete("/api/cofre/reset", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/api/io/vault", status_code=status.HTTP_204_NO_CONTENT)
def reset_cofre(
    force: bool = Query(False),
    master_key: str = Depends(get_master_key),
    service: VaultService = Depends(get_vault_service),
) -> None:
    try:
        service.reset_vault(master_key, force=force)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e

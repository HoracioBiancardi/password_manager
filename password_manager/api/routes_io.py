"""Endpoints de exportação e importação de dados."""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from password_manager.exceptions import ChaveMestreInvalidaError
from password_manager.models.credencial import Credencial
from password_manager.models.nota import Nota
from password_manager.services.notas_service import NotasService
from password_manager.services.password_manager_service import PasswordManagerService

from .dependencies import get_notas_servico, get_servico

router = APIRouter(prefix="/io", tags=["import/export"])

_FORMAT_VERSION = 1


class ImportPayload(BaseModel):
    version: int = _FORMAT_VERSION
    senhas: list[dict] = []
    notas: list[dict] = []


@router.get("/export")
def exportar(
    servico: PasswordManagerService = Depends(get_servico),
    notas_servico: NotasService = Depends(get_notas_servico),
) -> JSONResponse:
    """Exporta todas as senhas e notas em formato JSON descriptografado."""
    try:
        senhas = [c.to_dict() for c in servico.listar_credenciais()]
        notas  = [n.to_dict() for n in notas_servico.listar()]
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")

    payload = {
        "version": _FORMAT_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "senhas": senhas,
        "notas": notas,
    }
    filename = f"pm-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import")
def importar(
    payload: ImportPayload,
    servico: PasswordManagerService = Depends(get_servico),
    notas_servico: NotasService = Depends(get_notas_servico),
) -> dict:
    """Importa senhas e notas, ignorando duplicatas já existentes."""
    try:
        senhas_existentes = servico.listar_credenciais()
        notas_existentes  = notas_servico.listar()
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")

    chaves_senhas = {(c.nome, c.email) for c in senhas_existentes}
    ids_notas     = {n.id for n in notas_existentes}

    senhas_importadas = notas_importadas = 0

    try:
        for d in payload.senhas:
            cred = Credencial.from_dict(d)
            if (cred.nome, cred.email) not in chaves_senhas:
                servico.adicionar_credencial(cred)
                chaves_senhas.add((cred.nome, cred.email))
                senhas_importadas += 1

        for d in payload.notas:
            nota = Nota.from_dict(d)
            if nota.id not in ids_notas:
                notas_servico.adicionar(nota)
                ids_notas.add(nota.id)
                notas_importadas += 1
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"Arquivo inválido: {exc}")

    return {
        "senhas_importadas": senhas_importadas,
        "notas_importadas": notas_importadas,
        "senhas_ignoradas": len(payload.senhas) - senhas_importadas,
        "notas_ignoradas": len(payload.notas) - notas_importadas,
    }

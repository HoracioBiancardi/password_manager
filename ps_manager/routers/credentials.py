from __future__ import annotations
from typing import Annotated
from urllib.parse import unquote
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from ps_manager.dependencies import get_vault_service
from ps_manager.models.schemas import (
    CredentialCreateRequest,
    CredentialResponse,
    CredentialUpdateRequest,
)
from ps_manager.services.vault_service import VaultService

router = APIRouter(prefix="/api/credenciais", tags=["credenciais"])

import time

_failed_attempts = 0
_lockout_until = 0.0

def check_rate_limit():
    global _lockout_until, _failed_attempts
    now = time.time()
    if now < _lockout_until:
        remaining = int(_lockout_until - now)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Muitas tentativas incorretas. Bloqueio temporário de {remaining}s."
        )

def record_failed_attempt():
    global _failed_attempts, _lockout_until
    _failed_attempts += 1
    if _failed_attempts >= 5:
        _lockout_until = time.time() + 30.0

def record_successful_attempt():
    global _failed_attempts, _lockout_until
    _failed_attempts = 0
    _lockout_until = 0.0

def get_master_key(x_master_key: Annotated[str | None, Header(alias="X-Master-Key")] = None) -> str:
    check_rate_limit()
    if not x_master_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header 'X-Master-Key' é obrigatório."
        )
    return x_master_key

@router.get("/", response_model=list[CredentialResponse])
def listar_credenciais(
    master_key: str = Depends(get_master_key),
    service: VaultService = Depends(get_vault_service),
) -> list[CredentialResponse]:
    try:
        res = [c.to_dict() for c in service.listar_credenciais(master_key)]
        record_successful_attempt()
        return res
    except PermissionError as e:
        record_failed_attempt()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e

@router.get("/buscar", response_model=list[CredentialResponse])
def buscar_credenciais(
    termo: Annotated[str, Query(description="Termo de busca")],
    master_key: str = Depends(get_master_key),
    service: VaultService = Depends(get_vault_service),
) -> list[CredentialResponse]:
    try:
        res = [c.to_dict() for c in service.listar_credenciais(master_key, busca=termo)]
        record_successful_attempt()
        return res
    except PermissionError as e:
        record_failed_attempt()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e

@router.post("/", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
def adicionar_credencial(
    body: CredentialCreateRequest,
    master_key: str = Depends(get_master_key),
    service: VaultService = Depends(get_vault_service),
) -> CredentialResponse:
    try:
        cred = service.adicionar_credencial(master_key, body.model_dump())
        record_successful_attempt()
        return cred.to_dict()
    except PermissionError as e:
        record_failed_attempt()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e

@router.put("/{key_str:path}", response_model=CredentialResponse)
def atualizar_credencial(
    key_str: str,
    body: CredentialUpdateRequest,
    master_key: str = Depends(get_master_key),
    service: VaultService = Depends(get_vault_service),
) -> CredentialResponse:
    try:
        unquoted = unquote(key_str)
        existing = service.buscar_credencial(master_key, unquoted)
        if not existing:
            cred_dict = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
            if "nome" not in cred_dict or "email" not in cred_dict or "senha" not in cred_dict:
                parts = unquoted.split("::", 1)
                if len(parts) == 2:
                    cred_dict.setdefault("nome", parts[0])
                    cred_dict.setdefault("email", parts[1])
            cred = service.adicionar_credencial(master_key, cred_dict)
            record_successful_attempt()
            return cred.to_dict()
        
        merged = existing.to_dict()
        for k, v in body.model_dump(exclude_unset=True).items():
            if v is not None:
                merged[k] = v
        
        cred = service.atualizar_credencial(master_key, unquoted, merged)
        record_successful_attempt()
        return cred.to_dict()
    except PermissionError as e:
        record_failed_attempt()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e

@router.delete("/{key_str:path}", status_code=status.HTTP_204_NO_CONTENT)
def remover_credencial(
    key_str: str,
    master_key: str = Depends(get_master_key),
    service: VaultService = Depends(get_vault_service),
) -> None:
    try:
        service.remover_credencial(master_key, unquote(key_str))
        record_successful_attempt()
    except PermissionError as e:
        record_failed_attempt()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
    except FileNotFoundError as e:
        record_successful_attempt()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

@router.post("/{key_str:path}/favorito", response_model=CredentialResponse)
def favoritar_credencial(
    key_str: str,
    master_key: str = Depends(get_master_key),
    service: VaultService = Depends(get_vault_service),
) -> CredentialResponse:
    try:
        cred = service.toggle_favorito(master_key, unquote(key_str))
        record_successful_attempt()
        return cred.to_dict()
    except PermissionError as e:
        record_failed_attempt()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e
    except FileNotFoundError as e:
        record_successful_attempt()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

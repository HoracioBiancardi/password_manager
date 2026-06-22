"""Endpoints da API de gerenciamento de senhas."""

from fastapi import APIRouter, Depends, HTTPException, Query

from password_manager.exceptions import ChaveMestreInvalidaError
from password_manager.models.credencial import Credencial
from password_manager.services.password_manager_service import PasswordManagerService

from .dependencies import get_servico
from .schemas import AtualizarIn, CredencialIn, CredencialOut

router = APIRouter(prefix="/credenciais", tags=["credenciais"])


@router.get("/", response_model=list[CredencialOut])
def listar(servico: PasswordManagerService = Depends(get_servico)) -> list[CredencialOut]:
    """Retorna todas as credenciais armazenadas."""
    try:
        return [CredencialOut(**c.to_dict()) for c in servico.listar_credenciais()]
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")


@router.get("/buscar", response_model=list[CredencialOut])
def buscar(
    termo: str = Query(..., description="Nome, URL ou e-mail para buscar"),
    servico: PasswordManagerService = Depends(get_servico),
) -> list[CredencialOut]:
    """Busca credenciais por nome, URL ou e-mail (case-insensitive, substring)."""
    try:
        return [CredencialOut(**c.to_dict()) for c in servico.buscar_credenciais(termo)]
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")


@router.post("/", status_code=201)
def adicionar(
    payload: CredencialIn,
    servico: PasswordManagerService = Depends(get_servico),
) -> dict[str, str]:
    """Adiciona uma nova credencial ao cofre criptografado."""
    try:
        servico.adicionar_credencial(Credencial(**payload.model_dump()))
        return {"detail": "Credencial adicionada."}
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")


@router.patch("/", response_model=CredencialOut)
def atualizar(
    payload: AtualizarIn,
    servico: PasswordManagerService = Depends(get_servico),
) -> CredencialOut:
    """Atualiza parcialmente uma credencial. Campos ausentes mantêm o valor atual."""
    try:
        correspondencias = servico.buscar_credenciais(payload.nome_atual)
        alvo = next(
            (
                c for c in correspondencias
                if c.nome == payload.nome_atual and c.email == payload.email_atual
            ),
            None,
        )
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")

    if alvo is None:
        raise HTTPException(status_code=404, detail="Credencial não encontrada.")

    nova = Credencial(
        nome=payload.nome if payload.nome is not None else alvo.nome,
        url=payload.url if payload.url is not None else alvo.url,
        email=payload.email if payload.email is not None else alvo.email,
        senha=payload.senha if payload.senha is not None else alvo.senha,
    )

    try:
        if not servico.atualizar_credencial(payload.nome_atual, payload.email_atual, nova):
            raise HTTPException(status_code=404, detail="Credencial não encontrada.")
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")

    return CredencialOut(**nova.to_dict())


@router.delete("/")
def remover(
    nome: str = Query(..., description="Nome exato do serviço"),
    email: str = Query(..., description="E-mail exato da credencial"),
    servico: PasswordManagerService = Depends(get_servico),
) -> dict[str, str]:
    """Remove uma credencial pelo nome e e-mail exatos."""
    try:
        if not servico.remover_credencial(nome, email):
            raise HTTPException(status_code=404, detail="Credencial não encontrada.")
        return {"detail": "Credencial removida."}
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")

"""Endpoints da API de gerenciamento de senhas."""

from fastapi import APIRouter, Depends, HTTPException, Query

from password_manager.exceptions import ChaveMestreInvalidaError
from password_manager.models.credencial import Credencial
from password_manager.services.password_manager_service import PasswordManagerService

from .dependencies import get_servico
from .schemas import AtualizarIn, CredencialIn, CredencialOut

router = APIRouter(prefix="/credenciais", tags=["credenciais"])


def _mesclar_credencial(payload: AtualizarIn, alvo: Credencial) -> Credencial:
    """Mescla um payload de atualização parcial sobre uma credencial existente.

    Args:
        payload: Payload recebido no PATCH. Campos None mantêm o valor atual.
        alvo: Credencial existente a ser usada como base para os campos ausentes.

    Returns:
        Nova instância de Credencial com os campos mesclados.
    """
    return Credencial(
        nome=payload.nome if payload.nome is not None else alvo.nome,
        url=payload.url if payload.url is not None else alvo.url,
        email=payload.email if payload.email is not None else alvo.email,
        senha=payload.senha if payload.senha is not None else alvo.senha,
        observacao=payload.observacao if payload.observacao is not None else alvo.observacao,
        tipo=payload.tipo if payload.tipo is not None else alvo.tipo,
        ambiente=payload.ambiente if payload.ambiente is not None else alvo.ambiente,
        expira_em=payload.expira_em if payload.expira_em is not None else alvo.expira_em,
        favorito=payload.favorito if payload.favorito is not None else alvo.favorito,
        tags=payload.tags if payload.tags is not None else alvo.tags,
    )


@router.get("/", response_model=list[CredencialOut])
def listar(servico: PasswordManagerService = Depends(get_servico)) -> list[CredencialOut]:
    """Retorna todas as credenciais armazenadas.

    Args:
        servico: Serviço de gerenciamento de senhas, injetado por dependência.

    Returns:
        Lista de todas as credenciais do cofre.

    Raises:
        HTTPException: Código 401 se a Chave Mestre for inválida.
    """
    try:
        return [CredencialOut(**c.to_dict()) for c in servico.listar_credenciais()]
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")


@router.get("/buscar", response_model=list[CredencialOut])
def buscar(
    termo: str = Query(..., description="Nome, URL ou e-mail para buscar"),
    servico: PasswordManagerService = Depends(get_servico),
) -> list[CredencialOut]:
    """Busca credenciais por nome, URL ou e-mail (case-insensitive, substring).

    Args:
        termo: Termo de busca aplicado a nome, URL e e-mail.
        servico: Serviço de gerenciamento de senhas, injetado por dependência.

    Returns:
        Lista de credenciais que correspondem ao termo buscado.

    Raises:
        HTTPException: Código 401 se a Chave Mestre for inválida.
    """
    try:
        return [CredencialOut(**c.to_dict()) for c in servico.buscar_credenciais(termo)]
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")


@router.post("/", status_code=201)
def adicionar(
    payload: CredencialIn,
    servico: PasswordManagerService = Depends(get_servico),
) -> dict[str, str]:
    """Adiciona uma nova credencial ao cofre criptografado.

    Args:
        payload: Dados da nova credencial.
        servico: Serviço de gerenciamento de senhas, injetado por dependência.

    Returns:
        Dicionário de confirmação com a chave 'detail'.

    Raises:
        HTTPException: Código 401 se a Chave Mestre for inválida.
    """
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
    """Atualiza parcialmente uma credencial. Campos ausentes mantêm o valor atual.

    Args:
        payload: Identificação da credencial (nome_atual/email_atual) e os campos
            a atualizar.
        servico: Serviço de gerenciamento de senhas, injetado por dependência.

    Returns:
        A credencial já atualizada.

    Raises:
        HTTPException: Código 401 se a Chave Mestre for inválida, ou 404 se a
            credencial não for encontrada.
    """
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

    nova = _mesclar_credencial(payload, alvo)

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
    """Remove uma credencial pelo nome e e-mail exatos.

    Args:
        nome: Nome exato do serviço a remover.
        email: E-mail exato da credencial a remover.
        servico: Serviço de gerenciamento de senhas, injetado por dependência.

    Returns:
        Dicionário de confirmação com a chave 'detail'.

    Raises:
        HTTPException: Código 401 se a Chave Mestre for inválida, ou 404 se a
            credencial não for encontrada.
    """
    try:
        if not servico.remover_credencial(nome, email):
            raise HTTPException(status_code=404, detail="Credencial não encontrada.")
        return {"detail": "Credencial removida."}
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")

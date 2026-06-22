"""Endpoints da API de notas seguras."""

from fastapi import APIRouter, Depends, HTTPException, Query

from password_manager.exceptions import ChaveMestreInvalidaError
from password_manager.models.nota import Nota
from password_manager.services.notas_service import NotasService

from .dependencies import get_notas_servico
from .schemas import NotaIn, NotaOut, AtualizarNotaIn

router = APIRouter(prefix="/notas", tags=["notas"])


@router.get("/", response_model=list[NotaOut])
def listar(servico: NotasService = Depends(get_notas_servico)) -> list[NotaOut]:
    try:
        return [NotaOut(**n.to_dict()) for n in servico.listar()]
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")


@router.get("/buscar", response_model=list[NotaOut])
def buscar(
    termo: str = Query(..., description="Texto a buscar no título ou conteúdo"),
    servico: NotasService = Depends(get_notas_servico),
) -> list[NotaOut]:
    try:
        return [NotaOut(**n.to_dict()) for n in servico.buscar(termo)]
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")


@router.post("/", status_code=201, response_model=NotaOut)
def adicionar(
    payload: NotaIn,
    servico: NotasService = Depends(get_notas_servico),
) -> NotaOut:
    try:
        nota = servico.adicionar(Nota(titulo=payload.titulo, conteudo=payload.conteudo))
        return NotaOut(**nota.to_dict())
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")


@router.patch("/{nota_id}", response_model=NotaOut)
def atualizar(
    nota_id: str,
    payload: AtualizarNotaIn,
    servico: NotasService = Depends(get_notas_servico),
) -> NotaOut:
    try:
        nota = servico.atualizar(nota_id, payload.titulo, payload.conteudo)
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")
    if nota is None:
        raise HTTPException(status_code=404, detail="Nota não encontrada.")
    return NotaOut(**nota.to_dict())


@router.delete("/{nota_id}")
def remover(
    nota_id: str,
    servico: NotasService = Depends(get_notas_servico),
) -> dict[str, str]:
    try:
        if not servico.remover(nota_id):
            raise HTTPException(status_code=404, detail="Nota não encontrada.")
        return {"detail": "Nota removida."}
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")

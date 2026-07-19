"""Endpoints de exportação e importação de dados."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse, Response
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
    """Payload de importação de um backup (JSON puro ou decifrado de um .enc).

    Attributes:
        version: Versão do formato de backup.
        senhas: Lista de credenciais no mesmo formato de Credencial.to_dict().
        notas: Reservado para uma futura funcionalidade de notas; atualmente
            aceito no payload mas não processado por _aplicar_importacao().
    """

    version: int = _FORMAT_VERSION
    senhas: list[dict[str, str | bool]] = []
    notas: list[dict[str, str]] = []


@router.get("/export")
def exportar(
    criptografado: bool = False,
    servico: PasswordManagerService = Depends(get_servico),
) -> Response:
    """Exporta todas as senhas, em JSON puro ou criptografadas com a Chave Mestre.

    Args:
        criptografado: Se True, o backup é criptografado com a mesma Chave Mestre
            do cofre (necessária para reimportá-lo depois) em vez de JSON puro.
        servico: Serviço de gerenciamento de senhas, injetado por dependência.

    Returns:
        Response com o backup como anexo para download (.json ou .enc).

    Raises:
        HTTPException: Código 401 se a Chave Mestre for inválida.
    """
    try:
        senhas = [c.to_dict() for c in servico.listar_credenciais()]
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")

    payload = {
        "version": _FORMAT_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "senhas": senhas,
    }
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    if criptografado:
        conteudo = servico.criptografar_payload(payload)
        filename = f"pm-backup-{timestamp}.enc"
        return Response(
            content=conteudo,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    filename = f"pm-backup-{timestamp}.json"
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/vault")
def reset_vault(x_master_key: str = Header(...)) -> dict[str, str]:
    """Apaga o cofre de senhas. Valida o formato da chave (sem descriptografar o vault).

    Args:
        x_master_key: Chave Mestre enviada no header X-Master-Key, usada apenas
            para validar o formato antes de apagar o arquivo do cofre.

    Returns:
        Dicionário de confirmação com a chave 'detail'.

    Raises:
        HTTPException: Código 401 se a Chave Mestre tiver formato inválido.
    """
    try:
        CryptoService(x_master_key)
    except ChaveMestreInvalidaError:
        raise HTTPException(status_code=401, detail="Chave Mestre inválida.")
    settings = Settings()
    settings.storage_path.unlink(missing_ok=True)
    return {"detail": "Cofre apagado."}


def _aplicar_importacao(servico: PasswordManagerService, payload: ImportPayload) -> dict:
    """Aplica os itens de um ImportPayload ao cofre, ignorando duplicatas já existentes.

    Args:
        servico: Serviço de gerenciamento de senhas usado para ler e gravar o cofre.
        payload: Itens a importar (deduplica por par nome+email).

    Returns:
        Dicionário com as contagens 'senhas_importadas' e 'senhas_ignoradas'.

    Raises:
        HTTPException: Código 401 se a Chave Mestre for inválida, ou 422 se algum
            item do payload estiver malformado.
    """
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


@router.post("/import")
def importar(
    payload: ImportPayload,
    servico: PasswordManagerService = Depends(get_servico),
) -> dict:
    """Importa senhas de um backup JSON puro, ignorando duplicatas já existentes.

    Args:
        payload: Backup JSON já desserializado no formato ImportPayload.
        servico: Serviço de gerenciamento de senhas, injetado por dependência.

    Returns:
        Dicionário com as contagens 'senhas_importadas' e 'senhas_ignoradas'.

    Raises:
        HTTPException: Código 401 se a Chave Mestre for inválida, ou 422 se o
            payload estiver malformado.
    """
    return _aplicar_importacao(servico, payload)


@router.post("/import-encrypted")
async def importar_criptografado(
    request: Request,
    servico: PasswordManagerService = Depends(get_servico),
) -> dict:
    """Importa senhas de um backup gerado por /export?criptografado=true.

    O corpo da requisição é o payload criptografado bruto (bytes); é decifrado
    com a mesma Chave Mestre do header X-Master-Key.

    Args:
        request: Requisição HTTP cujo corpo bruto é o backup criptografado.
        servico: Serviço de gerenciamento de senhas, injetado por dependência.

    Returns:
        Dicionário com as contagens 'senhas_importadas' e 'senhas_ignoradas'.

    Raises:
        HTTPException: Código 401 se a Chave Mestre não decifrar o backup, ou
            422 se o backup estiver corrompido ou malformado após decifrado.
    """
    corpo = await request.body()
    try:
        dados = servico.descriptografar_payload(corpo)
    except ChaveMestreInvalidaError:
        raise HTTPException(
            status_code=401,
            detail="Chave Mestre inválida para decriptar este backup.",
        )
    except Exception:
        raise HTTPException(status_code=422, detail="Arquivo de backup criptografado inválido ou corrompido.")

    try:
        payload = ImportPayload(**dados)
    except Exception:
        raise HTTPException(status_code=422, detail="Arquivo de backup criptografado inválido.")

    return _aplicar_importacao(servico, payload)

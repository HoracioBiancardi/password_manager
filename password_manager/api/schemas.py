"""Schemas Pydantic para requests e responses da API."""

from pydantic import BaseModel


# ── Notas ──────────────────────────────────────────────────────────────────

class NotaIn(BaseModel):
    titulo: str
    conteudo: str = ""


class NotaOut(BaseModel):
    id: str
    titulo: str
    conteudo: str
    criado_em: str
    atualizado_em: str


class AtualizarNotaIn(BaseModel):
    titulo: str
    conteudo: str


class CredencialIn(BaseModel):
    """Payload para criação de uma credencial."""

    nome: str
    url: str = ""
    email: str
    senha: str
    observacao: str = ""


class CredencialOut(BaseModel):
    """Representação de uma credencial na resposta da API."""

    nome: str
    url: str
    email: str
    senha: str
    observacao: str = ""


class AtualizarIn(BaseModel):
    """Payload para atualização parcial de uma credencial.

    Attributes:
        nome_atual: Nome exato do serviço que identifica a credencial.
        email_atual: E-mail exato que identifica a credencial.
        nome: Novo nome. None mantém o valor atual.
        url: Nova URL. None mantém o valor atual.
        email: Novo e-mail. None mantém o valor atual.
        senha: Nova senha. None mantém o valor atual.
        observacao: Nova observação. None mantém o valor atual.
    """

    nome_atual: str
    email_atual: str
    nome: str | None = None
    url: str | None = None
    email: str | None = None
    senha: str | None = None
    observacao: str | None = None

"""Schemas Pydantic para requests e responses da API."""

from pydantic import BaseModel


class CredencialIn(BaseModel):
    """Payload para criação de uma credencial.

    Attributes:
        nome: Nome descritivo do serviço ou sistema.
        url: URL do serviço. Opcional.
        email: Identificador, usuário ou e-mail de login.
        senha: Texto puro da senha, token ou secret.
        observacao: Anotação livre sobre a credencial.
        tipo: Categoria da credencial ('senha', 'token', 'api_key' ou 'secret').
        ambiente: Ambiente de uso ('dev', 'staging', 'prod' ou vazio).
        expira_em: Data de expiração em formato ISO ('YYYY-MM-DD'). Vazio significa
            sem expiração definida.
        favorito: Se True, a credencial é fixada no topo da lista no frontend.
        tags: Categorias em texto livre, separadas por vírgula.
    """

    nome: str
    url: str = ""
    email: str
    senha: str
    observacao: str = ""
    tipo: str = ""
    ambiente: str = ""
    expira_em: str = ""
    favorito: bool = False
    tags: str = ""


class CredencialOut(BaseModel):
    """Representação de uma credencial na resposta da API.

    Attributes:
        nome: Nome descritivo do serviço ou sistema.
        url: URL do serviço.
        email: Identificador, usuário ou e-mail de login.
        senha: Texto puro da senha, token ou secret.
        observacao: Anotação livre sobre a credencial.
        criado_em: Timestamp ISO de criação.
        atualizado_em: Timestamp ISO da última atualização.
        tipo: Categoria da credencial ('senha', 'token', 'api_key' ou 'secret').
        ambiente: Ambiente de uso ('dev', 'staging', 'prod' ou vazio).
        expira_em: Data de expiração em formato ISO ('YYYY-MM-DD'). Vazio significa
            sem expiração definida.
        favorito: Se True, a credencial é fixada no topo da lista no frontend.
        tags: Categorias em texto livre, separadas por vírgula.
    """

    nome: str
    url: str
    email: str
    senha: str
    observacao: str = ""
    criado_em: str = ""
    atualizado_em: str = ""
    tipo: str = ""
    ambiente: str = ""
    expira_em: str = ""
    favorito: bool = False
    tags: str = ""


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
        tipo: Nova categoria. None mantém o valor atual.
        ambiente: Novo ambiente. None mantém o valor atual.
        expira_em: Nova data de expiração. None mantém o valor atual.
        favorito: Novo estado de favorito. None mantém o valor atual.
        tags: Novas tags. None mantém o valor atual.
    """

    nome_atual: str
    email_atual: str
    nome: str | None = None
    url: str | None = None
    email: str | None = None
    senha: str | None = None
    observacao: str | None = None
    tipo: str | None = None
    ambiente: str | None = None
    expira_em: str | None = None
    favorito: bool | None = None
    tags: str | None = None

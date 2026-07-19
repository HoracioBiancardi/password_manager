"""Entidades de domínio do gerenciador de senhas."""

from dataclasses import dataclass


@dataclass
class Credencial:
    """Representa uma credencial de acesso no sistema.

    Attributes:
        nome: Nome descritivo do serviço (ex: 'Github').
        url: URL do serviço (ex: 'https://github.com'). Opcional.
        email: Identificador, usuário ou e-mail de login.
        senha: Texto puro da senha (disponível apenas em memória após descriptografia).
        observacao: Anotação livre sobre a credencial.
        criado_em: Timestamp ISO de criação, definido pela camada de serviço.
        atualizado_em: Timestamp ISO da última atualização, definido pela camada de serviço.
        tipo: Categoria da credencial ('senha', 'token', 'api_key' ou 'secret').
            Vazio é tratado como 'senha' para compatibilidade com registros antigos.
        ambiente: Ambiente de uso da credencial ('dev', 'staging', 'prod' ou vazio).
        expira_em: Data de expiração em formato ISO ('YYYY-MM-DD'). Vazio significa
            sem expiração definida.
        favorito: Se True, a credencial é fixada no topo da lista no frontend.
        tags: Lista de categorias em texto livre, separadas por vírgula (ex:
            'trabalho, infra'). Vazio significa sem tags.
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

    def to_dict(self) -> dict[str, str | bool]:
        """Serializa a credencial para um dicionário.

        Returns:
            Dicionário com os campos 'nome', 'url', 'email', 'senha', 'observacao',
            'criado_em', 'atualizado_em', 'tipo', 'ambiente', 'expira_em',
            'favorito' e 'tags'.
        """
        return {
            "nome": self.nome,
            "url": self.url,
            "email": self.email,
            "senha": self.senha,
            "observacao": self.observacao,
            "criado_em": self.criado_em,
            "atualizado_em": self.atualizado_em,
            "tipo": self.tipo,
            "ambiente": self.ambiente,
            "expira_em": self.expira_em,
            "favorito": self.favorito,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | bool]) -> "Credencial":
        """Cria uma Credencial a partir de um dicionário.

        Args:
            data: Dicionário com chaves 'nome', 'url', 'email' e 'senha'.
                Os campos 'url', 'observacao', 'criado_em', 'atualizado_em', 'tipo',
                'ambiente', 'expira_em', 'favorito' e 'tags' são opcionais para
                compatibilidade com dados antigos.

        Returns:
            Instância de Credencial populada.
        """
        return cls(
            nome=data["nome"],
            url=data.get("url", ""),
            email=data["email"],
            senha=data["senha"],
            observacao=data.get("observacao", ""),
            criado_em=data.get("criado_em", ""),
            atualizado_em=data.get("atualizado_em", ""),
            tipo=data.get("tipo", ""),
            ambiente=data.get("ambiente", ""),
            expira_em=data.get("expira_em", ""),
            favorito=bool(data.get("favorito", False)),
            tags=data.get("tags", ""),
        )

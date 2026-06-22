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
    """

    nome: str
    url: str
    email: str
    senha: str
    observacao: str = ""

    def to_dict(self) -> dict[str, str]:
        """Serializa a credencial para um dicionário.

        Returns:
            Dicionário com os campos 'nome', 'url', 'email', 'senha' e 'observacao'.
        """
        return {
            "nome": self.nome,
            "url": self.url,
            "email": self.email,
            "senha": self.senha,
            "observacao": self.observacao,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "Credencial":
        """Cria uma Credencial a partir de um dicionário.

        Args:
            data: Dicionário com chaves 'nome', 'url', 'email' e 'senha'.
                Os campos 'url' e 'observacao' são opcionais para compatibilidade com dados antigos.

        Returns:
            Instância de Credencial populada.
        """
        return cls(
            nome=data["nome"],
            url=data.get("url", ""),
            email=data["email"],
            senha=data["senha"],
            observacao=data.get("observacao", ""),
        )

"""Interface de abstração para persistência de dados (DIP)."""

from abc import ABC, abstractmethod


class StorageInterface(ABC):
    """Contrato para implementações de persistência de dados criptografados.

    Aplica o princípio de Inversão de Dependência (DIP), permitindo trocar
    o mecanismo de armazenamento sem alterar as regras de negócio.
    """

    @abstractmethod
    def salvar_dados(self, dados_criptografados: bytes) -> None:
        """Persiste o payload criptografado no meio de armazenamento.

        Args:
            dados_criptografados: Bytes criptografados a serem persistidos.
        """

    @abstractmethod
    def carregar_dados(self) -> bytes:
        """Recupera os bytes criptografados do meio de armazenamento.

        Returns:
            Bytes criptografados, ou b"" se o repositório estiver vazio.
        """

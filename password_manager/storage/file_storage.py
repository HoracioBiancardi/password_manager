"""Implementação de armazenamento em arquivo físico."""

from pathlib import Path

from .interface import StorageInterface


class FileStorage(StorageInterface):
    """Persiste dados criptografados em um arquivo binário local.

    Attributes:
        _caminho: Caminho do arquivo de dados.
    """

    def __init__(self, caminho_arquivo: Path) -> None:
        """Inicializa o gerenciador de arquivo.

        Args:
            caminho_arquivo: Caminho para o arquivo de dados criptografados.
        """
        self._caminho: Path = caminho_arquivo

    def salvar_dados(self, dados_criptografados: bytes) -> None:
        """Grava os bytes no arquivo local.

        Args:
            dados_criptografados: Payload a ser gravado.
        """
        self._caminho.write_bytes(dados_criptografados)

    def carregar_dados(self) -> bytes:
        """Lê o arquivo local.

        Returns:
            Bytes do arquivo, ou b"" se o arquivo não existir.
        """
        if not self._caminho.exists():
            return b""
        return self._caminho.read_bytes()

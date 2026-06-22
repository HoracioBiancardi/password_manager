"""Serviço de criptografia baseado em Fernet (AES-128-CBC + HMAC-SHA256)."""

from cryptography.fernet import Fernet, InvalidToken

from password_manager.exceptions import ChaveMestreInvalidaError


class CryptoService:
    """Encapsula o ciclo de vida de chaves e a transformação criptográfica dos dados.

    Utiliza a especificação Fernet: criptografia simétrica AES-128 em modo CBC
    com autenticação via HMAC-SHA256.
    """

    def __init__(self, chave_mestre: str) -> None:
        """Inicializa o serviço com uma chave mestre Fernet.

        Args:
            chave_mestre: Chave Fernet válida (base64url de 32 bytes).
                Pode ser gerada com CryptoService.gerar_nova_chave().

        Raises:
            ChaveMestreInvalidaError: Se o formato da chave for inválido.
        """
        try:
            self._fernet: Fernet = Fernet(chave_mestre.encode())
        except Exception as exc:
            raise ChaveMestreInvalidaError("Formato de chave inválido.") from exc

    @staticmethod
    def gerar_nova_chave() -> str:
        """Gera uma nova chave Fernet segura.

        Returns:
            String da chave em formato base64url.
        """
        return Fernet.generate_key().decode()

    def criptografar(self, texto: str) -> bytes:
        """Criptografa uma string em texto puro.

        Args:
            texto: Texto a ser criptografado.

        Returns:
            Payload criptografado em bytes.
        """
        return self._fernet.encrypt(texto.encode())

    def descriptografar(self, dados_criptografados: bytes) -> str:
        """Descriptografa um payload de bytes para string.

        Args:
            dados_criptografados: Bytes produzidos por criptografar().

        Returns:
            Texto original descriptografado.

        Raises:
            ChaveMestreInvalidaError: Se a chave for inválida ou o payload corrompido.
        """
        try:
            return self._fernet.decrypt(dados_criptografados).decode()
        except InvalidToken as exc:
            raise ChaveMestreInvalidaError(
                "Chave Mestre inválida ou arquivo corrompido."
            ) from exc

"""Serviço de criptografia baseado em Fernet (AES-128-CBC + HMAC-SHA256)."""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from password_manager.exceptions import ChaveMestreInvalidaError


class CryptoService:
    """Encapsula o ciclo de vida de chaves e a transformação criptográfica dos dados.

    Utiliza a especificação Fernet: criptografia simétrica AES-128 em modo CBC
    com autenticação via HMAC-SHA256.
    """

    def __init__(self, chave_mestre: str) -> None:
        """Inicializa o serviço com uma chave mestre Fernet ou senha personalizada.

        Args:
            chave_mestre: Chave Fernet válida (base64url de 32 bytes) ou senha comum.

        Raises:
            ChaveMestreInvalidaError: Se o formato for totalmente inutilizável (ex: string vazia).
        """
        if not chave_mestre:
            raise ChaveMestreInvalidaError("A chave mestre não pode ser vazia.")
            
        try:
            # Tenta inicializar com a chave fornecida diretamente (se for formato Fernet válido)
            self._fernet: Fernet = Fernet(chave_mestre.encode())
        except Exception:
            # Caso contrário (qualquer senha comum), derivamos a chave usando SHA-256
            hash_bytes = hashlib.sha256(chave_mestre.encode()).digest()
            chave_derivada = base64.urlsafe_b64encode(hash_bytes).decode()
            self._fernet = Fernet(chave_derivada.encode())

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

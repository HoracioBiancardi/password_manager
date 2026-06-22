"""Exceções de domínio do gerenciador de senhas."""


class ChaveMestreInvalidaError(Exception):
    """Levantada quando a chave mestre é inválida ou o arquivo está corrompido."""

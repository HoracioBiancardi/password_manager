"""Camada de serviço: orquestração das regras de negócio."""

import json

from password_manager.crypto.crypto_service import CryptoService
from password_manager.models.credencial import Credencial
from password_manager.storage.interface import StorageInterface


class PasswordManagerService:
    """Orquestra o ciclo de vida das credenciais: adição, busca e remoção.

    Recebe CryptoService e StorageInterface via injeção de dependências (DIP),
    garantindo que as regras de negócio não dependam de implementações concretas.
    """

    def __init__(self, crypto: CryptoService, storage: StorageInterface) -> None:
        """Inicializa o serviço com dependências injetadas.

        Args:
            crypto: Instância do serviço de criptografia configurado.
            storage: Instância do mecanismo de persistência.
        """
        self._crypto: CryptoService = crypto
        self._storage: StorageInterface = storage

    def _ler_repositorio(self) -> list[dict[str, str]]:
        """Carrega e descriptografa o repositório completo de credenciais.

        Returns:
            Lista de dicionários com as credenciais armazenadas.

        Raises:
            ChaveMestreInvalidaError: Se a chave for inválida ou o arquivo corrompido.
        """
        dados_raw: bytes = self._storage.carregar_dados()
        if not dados_raw:
            return []
        return json.loads(self._crypto.descriptografar(dados_raw))

    def _salvar_repositorio(self, lista: list[dict[str, str]]) -> None:
        """Serializa, criptografa e persiste a lista de credenciais.

        Args:
            lista: Lista de dicionários de credenciais a persistir.
        """
        self._storage.salvar_dados(self._crypto.criptografar(json.dumps(lista)))

    def adicionar_credencial(self, credencial: Credencial) -> None:
        """Adiciona uma nova credencial ao repositório criptografado.

        Args:
            credencial: Objeto Credencial a ser persistido.

        Raises:
            ChaveMestreInvalidaError: Se a chave fornecida for inválida.
        """
        banco: list[dict[str, str]] = self._ler_repositorio()
        banco.append(credencial.to_dict())
        self._salvar_repositorio(banco)

    def buscar_credenciais(self, termo: str) -> list[Credencial]:
        """Busca credenciais por correspondência em nome ou e-mail (case-insensitive).

        Args:
            termo: Texto a buscar no campo 'nome' ou 'email'.

        Returns:
            Lista de Credenciais que correspondem ao termo.

        Raises:
            ChaveMestreInvalidaError: Se a chave fornecida for inválida.
        """
        banco: list[dict[str, str]] = self._ler_repositorio()
        termo_lower: str = termo.lower()
        return [
            Credencial.from_dict(item)
            for item in banco
            if termo_lower in item["nome"].lower()
            or termo_lower in item["email"].lower()
            or termo_lower in item.get("url", "").lower()
        ]

    def listar_credenciais(self) -> list[Credencial]:
        """Retorna todas as credenciais armazenadas.

        Returns:
            Lista completa de Credenciais descriptografadas.

        Raises:
            ChaveMestreInvalidaError: Se a chave fornecida for inválida.
        """
        return [Credencial.from_dict(item) for item in self._ler_repositorio()]

    def atualizar_credencial(self, nome: str, email: str, nova: Credencial) -> bool:
        """Substitui a credencial identificada por (nome, email) por nova.

        Args:
            nome: Nome exato do serviço da credencial a atualizar.
            email: E-mail exato da credencial a atualizar.
            nova: Credencial com os novos dados.

        Returns:
            True se encontrada e atualizada, False se não encontrada.

        Raises:
            ChaveMestreInvalidaError: Se a chave fornecida for inválida.
        """
        banco: list[dict[str, str]] = self._ler_repositorio()
        for i, item in enumerate(banco):
            if item["nome"] == nome and item["email"] == email:
                banco[i] = nova.to_dict()
                self._salvar_repositorio(banco)
                return True
        return False

    def remover_credencial(self, nome: str, email: str) -> bool:
        """Remove uma credencial identificada por nome e e-mail exatos.

        Args:
            nome: Nome exato do serviço.
            email: E-mail exato da credencial.

        Returns:
            True se removida com sucesso, False se não encontrada.

        Raises:
            ChaveMestreInvalidaError: Se a chave fornecida for inválida.
        """
        banco: list[dict[str, str]] = self._ler_repositorio()
        banco_filtrado = [
            item for item in banco
            if not (item["nome"] == nome and item["email"] == email)
        ]
        if len(banco_filtrado) == len(banco):
            return False
        self._salvar_repositorio(banco_filtrado)
        return True

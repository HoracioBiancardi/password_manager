"""Camada de serviço para notas seguras."""

import json
from datetime import datetime, timezone

from password_manager.crypto.crypto_service import CryptoService
from password_manager.models.nota import Nota
from password_manager.storage.interface import StorageInterface


class NotasService:
    def __init__(self, crypto: CryptoService, storage: StorageInterface) -> None:
        self._crypto = crypto
        self._storage = storage

    def _ler(self) -> list[dict]:
        raw = self._storage.carregar_dados()
        if not raw:
            return []
        return json.loads(self._crypto.descriptografar(raw))

    def _salvar(self, lista: list[dict]) -> None:
        self._storage.salvar_dados(self._crypto.criptografar(json.dumps(lista)))

    def listar(self) -> list[Nota]:
        return [Nota.from_dict(d) for d in self._ler()]

    def buscar(self, termo: str) -> list[Nota]:
        t = termo.lower()
        return [
            Nota.from_dict(d) for d in self._ler()
            if t in d["titulo"].lower() or t in d.get("conteudo", "").lower()
        ]

    def adicionar(self, nota: Nota) -> Nota:
        banco = self._ler()
        banco.append(nota.to_dict())
        self._salvar(banco)
        return nota

    def atualizar(self, nota_id: str, titulo: str, conteudo: str) -> Nota | None:
        banco = self._ler()
        for i, d in enumerate(banco):
            if d["id"] == nota_id:
                d["titulo"] = titulo
                d["conteudo"] = conteudo
                d["atualizado_em"] = datetime.now(timezone.utc).isoformat()
                banco[i] = d
                self._salvar(banco)
                return Nota.from_dict(d)
        return None

    def remover(self, nota_id: str) -> bool:
        banco = self._ler()
        novo = [d for d in banco if d["id"] != nota_id]
        if len(novo) == len(banco):
            return False
        self._salvar(novo)
        return True

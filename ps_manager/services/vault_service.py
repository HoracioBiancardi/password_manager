from __future__ import annotations
from datetime import datetime, timezone
from ps_manager.domain.entities import Credential, VaultData
from ps_manager.repositories.base import AbstractVaultRepository

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _make_key(c: Credential) -> str:
    return f"{c.nome}::{c.email}"

class VaultService:
    def __init__(self, repository: AbstractVaultRepository) -> None:
        self._repo = repository

    def listar_credenciais(self, master_key: str, busca: str | None = None) -> list[Credential]:
        vault = self._repo.load_vault(master_key)
        senhas = vault.senhas

        if busca:
            q = busca.strip().lower()
            senhas = [
                c for c in senhas
                if q in c.nome.lower() or q in c.email.lower() or q in c.url.lower() or q in c.tags.lower()
            ]

        # Ordenar por favoritos primeiro, depois por nome
        senhas.sort(key=lambda c: (not c.favorito, c.nome.lower()))
        return senhas

    def buscar_credencial(self, master_key: str, key_str: str) -> Credential | None:
        vault = self._repo.load_vault(master_key)
        for c in vault.senhas:
            if _make_key(c) == key_str:
                return c
        return None

    def adicionar_credencial(self, master_key: str, cred_dict: dict) -> Credential:
        vault = self._repo.load_vault(master_key)
        now = _utc_now()
        
        cred = Credential.from_dict(cred_dict)
        cred.criado_em = now
        cred.atualizado_em = now

        # Verificar duplicata de chave (nome::email)
        new_key = _make_key(cred)
        vault.senhas = [c for c in vault.senhas if _make_key(c) != new_key]
        vault.senhas.append(cred)

        self._repo.save_vault(vault, master_key)
        return cred

    def atualizar_credencial(self, master_key: str, key_str: str, cred_dict: dict) -> Credential:
        vault = self._repo.load_vault(master_key)
        now = _utc_now()
        
        found_idx = None
        for i, c in enumerate(vault.senhas):
            if _make_key(c) == key_str:
                found_idx = i
                break

        if found_idx is None:
            raise FileNotFoundError(f"Credencial '{key_str}' não encontrada.")

        orig = vault.senhas[found_idx]
        updated = Credential.from_dict(cred_dict)
        updated.criado_em = orig.criado_em
        updated.atualizado_em = now

        vault.senhas[found_idx] = updated
        self._repo.save_vault(vault, master_key)
        return updated

    def remover_credencial(self, master_key: str, key_str: str) -> None:
        vault = self._repo.load_vault(master_key)
        initial_count = len(vault.senhas)
        vault.senhas = [c for c in vault.senhas if _make_key(c) != key_str]
        
        if len(vault.senhas) == initial_count:
            raise FileNotFoundError(f"Credencial '{key_str}' não encontrada.")

        self._repo.save_vault(vault, master_key)

    def toggle_favorito(self, master_key: str, key_str: str) -> Credential:
        vault = self._repo.load_vault(master_key)
        for c in vault.senhas:
            if _make_key(c) == key_str:
                c.favorito = not c.favorito
                c.atualizado_em = _utc_now()
                self._repo.save_vault(vault, master_key)
                return c
        raise FileNotFoundError(f"Credencial '{key_str}' não encontrada.")

    def exportar_vault(self, master_key: str) -> VaultData:
        return self._repo.load_vault(master_key)

    def importar_vault(self, master_key: str, new_senhas: list[dict]) -> dict[str, int]:
        vault = self._repo.load_vault(master_key)
        existing_keys = {_make_key(c) for c in vault.senhas}
        
        importados = 0
        ignorados = 0

        now = _utc_now()
        for raw in new_senhas:
            c = Credential.from_dict(raw)
            k = _make_key(c)
            if k in existing_keys:
                ignorados += 1
            else:
                if not c.criado_em:
                    c.criado_em = now
                if not c.atualizado_em:
                    c.atualizado_em = now
                vault.senhas.append(c)
                existing_keys.add(k)
                importados += 1

        self._repo.save_vault(vault, master_key)
        return {"senhas_importadas": importados, "senhas_ignoradas": ignorados}

    def reset_vault(self, master_key: str, force: bool = False) -> None:
        if not force and self._repo.vault_exists():
            self._repo.load_vault(master_key)
        empty_vault = VaultData(version=1, senhas=[])
        self._repo.save_vault(empty_vault, master_key)

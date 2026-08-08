from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class Credential:
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
    def from_dict(cls, data: dict[str, str | bool]) -> Credential:
        return cls(
            nome=str(data.get("nome", "")),
            url=str(data.get("url", "")),
            email=str(data.get("email", "")),
            senha=str(data.get("senha", "")),
            observacao=str(data.get("observacao", "")),
            criado_em=str(data.get("criado_em", "")),
            atualizado_em=str(data.get("atualizado_em", "")),
            tipo=str(data.get("tipo", "")),
            ambiente=str(data.get("ambiente", "")),
            expira_em=str(data.get("expira_em", "")),
            favorito=bool(data.get("favorito", False)),
            tags=str(data.get("tags", "")),
        )

@dataclass
class VaultData:
    version: int = 1
    senhas: list[Credential] = field(default_factory=list)

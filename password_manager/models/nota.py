"""Entidade de domínio para notas seguras."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid


@dataclass
class Nota:
    titulo: str
    conteudo: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    criado_em: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    atualizado_em: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "conteudo": self.conteudo,
            "criado_em": self.criado_em,
            "atualizado_em": self.atualizado_em,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "Nota":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            titulo=data["titulo"],
            conteudo=data.get("conteudo", ""),
            criado_em=data.get("criado_em", datetime.now(timezone.utc).isoformat()),
            atualizado_em=data.get("atualizado_em", datetime.now(timezone.utc).isoformat()),
        )

from __future__ import annotations
from pydantic import BaseModel, Field

class CredentialResponse(BaseModel):
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

class CredentialCreateRequest(BaseModel):
    nome: str = Field(..., description="Nome do serviço")
    url: str = Field(default="", description="URL do serviço")
    email: str = Field(..., description="E-mail ou usuário")
    senha: str = Field(..., description="Senha")
    observacao: str = Field(default="", description="Anotações adicionais")
    tipo: str = Field(default="", description="Tipo: senha|token|api_key|secret")
    ambiente: str = Field(default="", description="Ambiente: dev|staging|prod")
    expira_em: str = Field(default="", description="Data de expiração YYYY-MM-DD")
    favorito: bool = Field(default=False)
    tags: str = Field(default="")

class CredentialUpdateRequest(BaseModel):
    nome: str | None = None
    url: str | None = None
    email: str | None = None
    senha: str | None = None
    observacao: str | None = None
    tipo: str | None = None
    ambiente: str | None = None
    expira_em: str | None = None
    favorito: bool | None = None
    tags: str | None = None

class VaultExportResponse(BaseModel):
    version: int
    senhas: list[CredentialResponse]

class VaultImportPayload(BaseModel):
    version: int = 1
    senhas: list[CredentialCreateRequest]

class VaultImportResponse(BaseModel):
    senhas_importadas: int
    senhas_ignoradas: int

# Password Manager

Gerenciador de senhas local com criptografia Fernet (AES-128-CBC + HMAC-SHA256), interface CLI, API REST e página web de gestão.

## Funcionalidades

- Criptografia simétrica com chave mestre Fernet
- CLI completa: adicionar, buscar, atualizar, listar e remover
- API REST local (FastAPI) com autenticação por header
- Interface web servida pela própria API
- Busca por nome de serviço, URL ou e-mail (case-insensitive)
- Chave mestre digitada a cada uso ou salva em `.env` local
- Arquitetura SOLID com injeção de dependências

## Tecnologias

- Python 3.10+
- [cryptography](https://cryptography.io) — Fernet
- [Typer](https://typer.tiangolo.com) + [Rich](https://rich.readthedocs.io) — CLI
- [FastAPI](https://fastapi.tiangolo.com) + [Uvicorn](https://www.uvicorn.org) — API e frontend
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) — configuração via `.env`
- [uv](https://docs.astral.sh/uv/) — gerenciamento de dependências

## Instalação

```bash
# Clonar e entrar no diretório
git clone <repo-url>
cd password_manager

# Criar ambiente virtual e instalar
uv venv
uv pip install -e .
```

## Configuração inicial

```bash
# Ativar o ambiente
source .venv/bin/activate

# Gerar a chave mestre e salvar no .env
pm gerar-chave --salvar
```

A chave é salva em `.password-manager/.env`. **Guarde uma cópia em local seguro — sem ela as senhas não podem ser recuperadas.**

> O diretório `.password-manager/` está no `.gitignore` e nunca será versionado.

## CLI

```bash
pm gerar-chave          # Gera uma nova chave mestre
pm gerar-chave --salvar # Gera e salva no .env

pm adicionar            # Adiciona uma credencial
pm buscar <termo>       # Busca por nome, URL ou e-mail
pm atualizar <termo>    # Edita uma credencial existente
pm listar               # Lista serviços e e-mails (sem senhas)
pm remover <termo>      # Remove uma credencial
```

Se `MASTER_KEY` estiver no `.env`, a chave é carregada automaticamente. Caso contrário, é solicitada via prompt.

## Interface web e API

```bash
pm-api
# Servidor em http://127.0.0.1:8000
# Documentação: http://127.0.0.1:8000/docs
```

Acesse `http://127.0.0.1:8000` no navegador para a interface de gestão.

### Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/` | Interface web |
| `GET` | `/health` | Status da API |
| `GET` | `/credenciais/` | Listar todas |
| `GET` | `/credenciais/buscar?termo=...` | Buscar |
| `POST` | `/credenciais/` | Adicionar |
| `PATCH` | `/credenciais/` | Atualizar |
| `DELETE` | `/credenciais/?nome=...&email=...` | Remover |

Todas as rotas (exceto `/` e `/health`) exigem o header `X-Master-Key`.

## Estrutura do projeto

```
password_manager/
├── password_manager/
│   ├── models/
│   │   └── credencial.py          # Entidade Credencial
│   ├── storage/
│   │   ├── interface.py           # StorageInterface (DIP)
│   │   └── file_storage.py        # Persistência em arquivo .enc
│   ├── crypto/
│   │   └── crypto_service.py      # Criptografia Fernet
│   ├── services/
│   │   └── password_manager_service.py  # Regras de negócio
│   ├── api/
│   │   ├── app.py                 # FastAPI app
│   │   ├── routes.py              # Endpoints
│   │   ├── schemas.py             # Schemas Pydantic
│   │   └── dependencies.py        # Injeção de dependências
│   ├── frontend/
│   │   └── index.html             # Interface web
│   ├── config.py                  # Pydantic Settings
│   └── exceptions.py              # ChaveMestreInvalidaError
├── pyproject.toml
└── .gitignore
```

## Segurança

- As senhas são armazenadas em `.password-manager/senhas.enc` — criptografadas e nunca em texto puro no disco
- A chave mestre nunca é armazenada pelo servidor; ela trafega apenas pelo header `X-Master-Key` em cada requisição
- O diretório `.password-manager/` está no `.gitignore`
- A API escuta somente em `127.0.0.1` (localhost)

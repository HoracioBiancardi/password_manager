# Password Manager (PM Vault)

Gerenciador de senhas local com criptografia Fernet (AES-128-CBC + HMAC-SHA256), API REST (FastAPI) e interface web servida pela própria API — sem envio de dados para servidores externos. Além de senhas de sites, também guarda segredos de sistema-a-sistema (tokens, API keys) com ambiente e data de expiração. Inclui também uma extensão de navegador e um bookmarklet para preencher formulários de login automaticamente.

> Não há mais CLI neste projeto (foi removida — veja o histórico do git). Todo o uso é feito pela API + interface web.

## Funcionalidades

- Criptografia simétrica com chave mestre Fernet; a chave nunca é armazenada pelo servidor
- API REST local (FastAPI) com autenticação por header `X-Master-Key`, servida junto com a interface web
- Busca por nome de serviço, URL ou e-mail (case-insensitive)
- Indicador de força de senha e detecção de senhas reutilizadas (com filtro rápido) na lista
- Credenciais categorizadas por tipo (senha/token/api_key/secret) e ambiente (dev/staging/prod), pensadas
  também para segredos de sistema-a-sistema, não só senhas de site
- Alerta de expiração: badge por credencial e resumo ao desbloquear o cofre quando a data de expiração
  estiver próxima (limite configurável em Configurações > Alertas, padrão 30 dias) — os campos novos
  trafegam pelos mesmos endpoints `POST`/`PATCH /api/credenciais/` já existentes
- Ordenação da lista por nome, data de atualização ou domínio
- Ações rápidas no hover de cada credencial: copiar e-mail, copiar senha, abrir URL, excluir
- Bloqueio automático do cofre por inatividade (configurável em Configurações > Segurança)
- Exportação em JSON puro ou em backup criptografado (`.enc`) com a própria Chave Mestre
- Importação de JSON, backup criptografado (`.enc`) ou CSV exportado do Chrome/Edge/Brave/Firefox
- Extensão de navegador (Manifest V3) e bookmarklet para autofill de credenciais em qualquer site
- Chave mestre digitada a cada uso, com opção de "lembrar" (localStorage) ou manter só na sessão (sessionStorage)
- Arquitetura SOLID com injeção de dependências

## Tecnologias

- Python 3.10+
- [cryptography](https://cryptography.io) — Fernet
- [FastAPI](https://fastapi.tiangolo.com) + [Uvicorn](https://www.uvicorn.org) — API e frontend
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) — configuração via `.env`
- [uv](https://docs.astral.sh/uv/) — gerenciamento de dependências
- JavaScript puro (ES modules), sem framework nem build step, no frontend

## Instalação

```bash
# Clonar e entrar no diretório
git clone <repo-url>
cd password_manager

# Criar ambiente virtual e instalar
uv venv
uv pip install -e .
```

## Executando

```bash
source .venv/bin/activate
pm
# → http://127.0.0.1:8080         (interface web)
# → http://127.0.0.1:8080/docs    (documentação OpenAPI)
```

Na primeira execução, digite a chave mestre desejada na tela de login — o cofre é criado automaticamente na primeira credencial salva. **Guarde essa chave em local seguro: sem ela, os dados criptografados não podem ser recuperados.** A chave também pode ser fixada em `.password-manager/.env` (variável `MASTER_KEY`) para não precisar digitá-la — não recomendado em máquinas compartilhadas.

> O diretório `.password-manager/` (contém `.env` e o cofre `senhas.enc`) está no `.gitignore` e nunca é versionado.

## Endpoints da API

Todas as rotas abaixo (exceto `/` e `/health`) exigem o header `X-Master-Key`.

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/` | Interface web |
| `GET` | `/health` | Status da API |
| `GET` | `/api/credenciais/` | Listar todas |
| `GET` | `/api/credenciais/buscar?termo=...` | Buscar por nome, URL ou e-mail |
| `POST` | `/api/credenciais/` | Adicionar |
| `PATCH` | `/api/credenciais/` | Atualizar |
| `DELETE` | `/api/credenciais/?nome=...&email=...` | Remover |
| `GET` | `/api/io/export?criptografado=false` | Exportar (JSON puro ou `.enc`) |
| `POST` | `/api/io/import` | Importar backup JSON |
| `POST` | `/api/io/import-encrypted` | Importar backup `.enc` |
| `DELETE` | `/api/io/vault` | Apagar todo o cofre |

## Extensão de navegador e bookmarklet

Para preencher formulários de login automaticamente:

- **Extensão** (recomendada): Manifest V3, funciona em qualquer site. Veja `browser-extension/README.md` para instalar via `chrome://extensions`.
- **Bookmarklet**: alternativa sem instalação, arrastada para a barra de favoritos a partir da própria interface web. Sites com política de segurança de conteúdo (CSP) restritiva — GitHub, Google, redes sociais, bancos — bloqueiam scripts de bookmarklet; nesses casos, use a extensão.

Ambos conversam diretamente com a API local (`http://127.0.0.1:8080/api`), então o servidor (`pm`) precisa estar rodando.

## Estrutura do projeto

```
password_manager/
├── password_manager/
│   ├── models/
│   │   └── credencial.py          # Entidade Credencial (com criado_em/atualizado_em/tipo/ambiente/expira_em)
│   ├── storage/
│   │   ├── interface.py           # StorageInterface (DIP)
│   │   └── file_storage.py        # Persistência em arquivo .enc
│   ├── crypto/
│   │   └── crypto_service.py      # Criptografia Fernet
│   ├── services/
│   │   └── password_manager_service.py  # Regras de negócio
│   ├── api/
│   │   ├── app.py                 # FastAPI app, entrypoint `pm`
│   │   ├── routes.py              # /api/credenciais/*
│   │   ├── routes_io.py           # /api/io/* (export/import/reset)
│   │   ├── schemas.py             # Schemas Pydantic
│   │   └── dependencies.py        # Injeção de dependências
│   ├── frontend/
│   │   ├── index.html             # Interface web
│   │   ├── js/                    # app.js, api.js, state.js, prefs.js, utils.js
│   │   └── css/                   # theme.css, app.css
│   ├── config.py                  # Pydantic Settings
│   └── exceptions.py              # ChaveMestreInvalidaError
├── browser-extension/              # Extensão Manifest V3 + instruções de instalação
├── pyproject.toml
└── .gitignore
```

## Segurança

- As senhas são armazenadas em `.password-manager/senhas.enc` — criptografadas e nunca em texto puro no disco
- A chave mestre nunca é armazenada pelo servidor; ela trafega apenas pelo header `X-Master-Key` em cada requisição, e no frontend fica só em localStorage/sessionStorage (client-side)
- O diretório `.password-manager/` está no `.gitignore`
- A API escuta somente em `127.0.0.1` (localhost); o CORS é aberto (`allow_origins=["*"]`) por ser uma ferramenta local de usuário único
- O cofre pode ser bloqueado automaticamente por inatividade (Configurações > Segurança)

## Testes

Não há testes automatizados no repositório ainda (`pytest` está listado como dependência de desenvolvimento em `pyproject.toml`, mas não há arquivos de teste). Também não há lint/format configurado.

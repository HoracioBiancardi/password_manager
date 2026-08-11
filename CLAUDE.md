# CLAUDE.md — Contexto e Diretrizes do Password Manager

## Visão Geral do Projeto
O **Password Manager** é o gerenciador de senhas e cofre seguro de credenciais refatorado sob a arquitetura **SwordPower Starter Kit Universal** (**FastAPI + Vanilla JS ES Modules + CSS Variables + Pytest**).

---

## 🛠️ Comandos de Execução e Testes

```bash
# Entrar no diretório do projeto
cd /home/swordpower/Documentos/REPO/PESSOAL/password_manager

# Executar o Servidor de Desenvolvimento via uv run (Recomendado)
uv run uvicorn password_manager.main:app --reload --port 8003

# Alternativa direta com python
python3 -m uvicorn password_manager.main:app --reload --port 8003

# Executar a Suíte Completa de Testes Automatizados (Pytest)
uv run pytest -v
```

- **URL Web Local**: `http://127.0.0.1:8003`

---

## 📐 Serviços Padronizados

- **`crypto_vault_service.py`**: Cifragem Fernet AES-128 + PBKDF2 (600k iterações), Gerador de Senhas e Avaliador de Força de Senhas (`evaluate_password_strength`).
- **`db_service.py`**: Banco de dados SQLite WAL mode.
- **`task_runner_service.py`**: Executor de rotinas assíncronas em segundo plano.
- **`log_buffer_service.py`**: Console de logs de auditoria em memória.
- **`notification_service.py`**: Despachante de alertas para webhooks.
- **`log_buffer_service.py`** tem `LogBufferHandler` anexado ao logger raiz para captura automática de `logging.getLogger(__name__)` de qualquer módulo.

### Rotas de sistema (paridade com o app_template, só backend — sem UI própria)
- `GET /api/system/health`, `/metrics`, `/logs`, `POST /logs/clear`.
- `POST /api/vault/encrypt`, `/decrypt`, `/generate-password` (router `vault_tools.py` — não confundir com o router de domínio `vault.py`, que expõe `/api/cofre` e `/api/io`).
- `POST /api/tasks/start-demo`, `GET /list`, `GET /{task_id}`, `POST /{task_id}/cancel`.

---

## 🎨 Interface & Segurança
- Zero-Disk Storage (chaves mestre e tokens mantidos apenas em memória RAM).
- Auto-lock por inatividade programável.
- Temas: `corporate`, `green-neutral` e `cyber-dark`.

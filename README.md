# Password Manager — Cofre Seguro de Senhas

Aplicação de gerenciamento de credenciais e senhas criptografadas baseada no **SwordPower Starter Kit Universal**.

---

## ✨ Recursos de Segurança & Funcionalidades

- **Criptografia Forte**: PBKDF2 (600.000 iterações + Salt) com Fernet AES-128.
- **Avaliador & Gerador de Senhas**: Cálculo de força (score 0-100), nível de segurança e recomendações.
- **Zero-Disk Master Key**: A chave mestre nunca é salva em disco, permanecendo apenas na RAM durante a sessão.
- **Auto-lock por Inatividade**: Bloqueio programável automático do cofre.
- **Serviços Backend**: `crypto_vault_service`, `db_service`, `task_runner_service`, `log_buffer_service`, `notification_service`, com rotas de paridade `/api/system`, `/api/vault` e `/api/tasks` (só backend, sem UI própria).
- **Suporte aos 3 Temas**: `corporate`, `green-neutral` e `cyber-dark`.

---

## 🚀 Como Executar

```bash
# Entrar no diretório
cd /home/swordpower/Documentos/REPO/PESSOAL/password_manager

# Iniciar o servidor
python3 -m uvicorn password_manager.main:app --reload --port 8001
```

Acesse em: **`http://127.0.0.1:8001`**

---

## 🧪 Suíte de Testes Automatizados

```bash
PYTHONPATH=. /home/swordpower/snap/antigravity/5/.local/bin/pytest -v
```

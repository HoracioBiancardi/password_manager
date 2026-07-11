# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Local password manager ("PM Vault"): FastAPI backend + vanilla JS frontend + a browser extension/bookmarklet for autofill. Passwords are encrypted at rest with Fernet (AES-128-CBC + HMAC-SHA256) and never stored server-side — the master key travels only in the `X-Master-Key` request header and is held client-side (localStorage/sessionStorage/chrome.storage).

There is no CLI anymore (it was removed — see git history); everything goes through the API + web UI.

## Commands

```bash
# Install (uv-managed project)
uv venv
uv pip install -e .

# Run the API + web UI
source .venv/bin/activate
pm
# → http://127.0.0.1:8080  (web UI)
# → http://127.0.0.1:8080/docs  (OpenAPI docs)
```

There are no automated tests in the repo yet (`pytest` is a listed dev dependency in `pyproject.toml` but no test files exist). There is no lint/format tooling configured.

The `pm` console script (defined in `pyproject.toml`, `password_manager.api.app:start`) starts the Uvicorn server. Note: `README.md` refers to a `pm-api` script and port 8000 — both are stale; the actual entry point is `pm` on port **8080** (`password_manager/api/app.py`).

## Architecture

Backend follows a SOLID/DIP layered design under `password_manager/`:

```
models/credencial.py          → Credencial dataclass (nome, url, email, senha, observacao)
storage/interface.py          → StorageInterface (ABC): salvar_dados/carregar_dados
storage/file_storage.py       → FileStorage: writes/reads the encrypted blob to .password-manager/senhas.enc
crypto/crypto_service.py      → CryptoService: Fernet encrypt/decrypt; derives a key via SHA-256 if the
                                 provided master key isn't already a valid Fernet key (so plain passwords work too)
services/password_manager_service.py → PasswordManagerService: business logic (add/search/list/update/remove).
                                 Reads the *entire* credential list, decrypts it as one JSON blob, mutates,
                                 re-encrypts, writes back — there is no per-record storage.
api/dependencies.py           → get_servico(): FastAPI dependency that reads X-Master-Key header per request,
                                 builds Settings() → FileStorage → CryptoService → PasswordManagerService fresh
                                 each time. Nothing is cached/persisted server-side between requests.
api/routes.py                 → /api/credenciais/* CRUD endpoints
api/routes_io.py              → /api/io/* export (JSON download), import (dedupes by nome+email), and
                                 vault reset (deletes the .enc file after validating key format only)
api/schemas.py                → Pydantic request/response models
api/app.py                    → create_app(): wires routers, serves frontend/index.html at "/", mounts
                                 frontend/ as static, defines start() entrypoint
config.py                     → Settings (pydantic-settings): master_key/storage_path, loaded from
                                 .password-manager/.env (gitignored, never versioned)
exceptions.py                 → ChaveMestreInvalidaError — the one domain exception, raised on bad/missing
                                 key or corrupted ciphertext, mapped to HTTP 401 in every route
```

Key invariant: every write to the vault happens via `_ler_repositorio()` → mutate list → `_salvar_repositorio()` in `PasswordManagerService`. There's no locking or partial-update mechanism, so concurrent writes can clobber each other — acceptable for a single-user local tool but worth knowing before adding features.

### Frontend (`password_manager/frontend/`)

Plain ES modules, no build step or framework:

- `js/state.js` — single shared mutable `st` object (masterKey, credentials, filtered, active/editing state)
- `js/api.js` — thin fetch wrapper (`apiFetch`) that injects `X-Master-Key` and normalizes 401s into `{status: 401}` errors
- `js/app.js` — all UI logic: auth flow, list/detail/edit rendering, CRUD calls, import/export, vault reset (imports from api.js/state.js/utils.js/prefs.js)
- `js/prefs.js` — "Pip-Boy CRT" visual theme preferences (scanlines, flicker, static, curved screen, color theme), persisted to localStorage and applied on boot
- `js/utils.js` — toast notifications, clipboard copy, blob download, misc DOM helpers
- `css/design-system.css` + `css/app.css` — the CRT/retro design system and app-specific styles

The master key is asked for at login and kept only client-side; "remember" checkbox chooses localStorage vs sessionStorage persistence.

### Browser extension (`browser-extension/`)

Manifest V3 extension (Chrome/Firefox) + a bookmarklet, for autofilling credentials from the local vault into arbitrary sites:

- `manifest.json` — permissions: `activeTab`, `storage`; content script runs on `<all_urls>`
- `popup.js` — talks to `http://127.0.0.1:8080/api` directly (hardcoded), stores the master key in `chrome.storage.local`, matches the active tab's domain against stored credentials
- `content.js` — injected into pages to fill detected login forms

This is a separate, unbundled artifact loaded manually via `chrome://extensions` (see `browser-extension/README.md` for install steps) — it is not built or packaged by the Python project.

## Security-relevant conventions

- Never log or persist the master key or plaintext passwords server-side; `PasswordManagerService`/`FileStorage` only ever handle ciphertext except transiently in memory.
- `.password-manager/` (contains `.env` with the key and `senhas.enc`) is gitignored — never commit anything from it, and don't add sample/real vault files to the repo.
- API binds to `127.0.0.1` only; CORS is wide open (`allow_origins=["*"]`) because it's assumed to be a local single-user tool — be cautious about tightening/loosening this without understanding that assumption.
- Domain terms are in Portuguese throughout (`credencial`, `chave_mestre`, `adicionar`, etc.) — match existing naming when extending this code rather than mixing in English identifiers.

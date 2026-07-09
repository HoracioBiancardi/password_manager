# PM Vault — Extensão & Bookmarklet

Esta pasta contém a extensão de navegador e o bookmarklet de auto-preenchimento de senhas para o **PM Vault** local.

---

## 🚀 Como instalar a Extensão

### Google Chrome / Brave / Edge / Opera (Chromium)
1. Abra o navegador e vá para a página de extensões: `chrome://extensions/`
2. Ative o **"Modo do desenvolvedor"** (canto superior direito).
3. Clique em **"Carregar sem compactação"** (canto superior esquerdo).
4. Selecione esta pasta `browser-extension` que contém o arquivo `manifest.json`.
5. Fixe a extensão na barra de ferramentas clicando no ícone de quebra-cabeça 🧩.

### Mozilla Firefox
1. Abra o Firefox e acesse a página: `about:debugging`
2. Clique em **"Este Firefox"** (na barra lateral esquerda).
3. Clique em **"Carregar manifesto temporário..."**.
4. Selecione o arquivo `manifest.json` dentro da pasta `browser-extension`.
5. A extensão estará ativa temporariamente (enquanto o Firefox estiver aberto).

---

## 📑 Bookmarklet (Solução Sem Instalação / Favorito)

Se você estiver em um computador corporativo ou com políticas de segurança restritas que impedem o carregamento de extensões não oficiais:

### Como usar o Bookmarklet
1. Abra a página principal do PM Vault no seu servidor local: `http://127.0.0.1:8080/`
2. Clique no botão **⚙️ Aparência** (no login ou na barra superior) e vá para a aba **"Integração"**.
3. Arraste o botão verde **"Preencher com PM Vault"** para a sua Barra de Favoritos.
4. Quando estiver em qualquer site (ex: `github.com`), clique no favorito criado.
5. Um pequeno painel retrô verde aparecerá no topo direito. Insira a sua chave mestre (ela é salva apenas na aba atual) e clique em "Buscar". Suas contas cadastradas para o site atual serão sugeridas. Clique sobre ela para preencher!

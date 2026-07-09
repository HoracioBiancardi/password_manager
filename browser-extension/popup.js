const API_URL = 'http://127.0.0.1:8080/api';
let currentKey = null;
let activeTab = null;

// DOM Screens
const screenAuth = document.getElementById('screen-auth');
const screenMain = document.getElementById('screen-main');
const screenAdd = document.getElementById('screen-add');

// DOM Elements - Auth
const inputKey = document.getElementById('input-key');
const btnSaveKey = document.getElementById('btn-save-key');

// DOM Elements - Main
const inputSearch = document.getElementById('input-search');
const btnShowAdd = document.getElementById('btn-show-add');
const credContainer = document.getElementById('cred-container');
const suggestionsTitle = document.getElementById('suggestions-title');
const domainLabel = document.getElementById('domain-label');
const linkLock = document.getElementById('link-lock');

// DOM Elements - Add
const addNome = document.getElementById('add-nome');
const addUrl = document.getElementById('add-url');
const addEmail = document.getElementById('add-email');
const addSenha = document.getElementById('add-senha');
const btnSaveCred = document.getElementById('btn-save-cred');
const btnCancelAdd = document.getElementById('btn-cancel-add');

// Initial Load
document.addEventListener('DOMContentLoaded', async () => {
  // Get active tab domain
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tabs && tabs[0]) {
    activeTab = tabs[0];
    try {
      const url = new URL(activeTab.url);
      domainLabel.textContent = url.hostname.replace(/^www\./, '');
    } catch {
      domainLabel.textContent = 'localhost';
    }
  }

  const storage = await chrome.storage.local.get(['pm_master_key']);
  if (storage.pm_master_key) {
    currentKey = storage.pm_master_key;
    showMainScreen();
  } else {
    showAuthScreen();
  }
});

// Auth Screen Action
btnSaveKey.addEventListener('click', async () => {
  const key = inputKey.value.trim();
  if (!key) return;
  
  btnSaveKey.disabled = true;
  btnSaveKey.textContent = 'Verificando...';

  try {
    const res = await fetch(`${API_URL}/credenciais/`, {
      headers: { 'X-Master-Key': key }
    });

    if (res.status === 401) {
      alert('Chave Mestre inválida ou incorreta.');
      btnSaveKey.disabled = false;
      btnSaveKey.textContent = 'Desbloquear Extensão';
      return;
    }

    if (!res.ok) {
      throw new Error('Servidor indisponível.');
    }

    await chrome.storage.local.set({ pm_master_key: key });
    currentKey = key;
    inputKey.value = '';
    showMainScreen();
  } catch (err) {
    alert('Erro ao conectar à API local do PM Vault. Certifique-se de que o servidor está rodando em 127.0.0.1:8080.');
  } finally {
    btnSaveKey.disabled = false;
    btnSaveKey.textContent = 'Desbloquear Extensão';
  }
});

// Search input
inputSearch.addEventListener('input', () => {
  loadCredentials(inputSearch.value.trim());
});

// Lock click
linkLock.addEventListener('click', async () => {
  await chrome.storage.local.remove('pm_master_key');
  currentKey = null;
  showAuthScreen();
});

// Add Credential Triggers
btnShowAdd.addEventListener('click', () => {
  showAddScreen();
});

btnCancelAdd.addEventListener('click', () => {
  showMainScreen();
});

btnSaveCred.addEventListener('click', async () => {
  const nome = addNome.value.trim();
  const url = addUrl.value.trim();
  const email = addEmail.value.trim();
  const senha = addSenha.value.trim();

  if (!nome || !email || !senha) {
    alert('Os campos Nome, E-mail/Usuário e Senha são obrigatórios.');
    return;
  }

  btnSaveCred.disabled = true;
  btnSaveCred.textContent = 'Salvando...';

  try {
    const res = await fetch(`${API_URL}/credenciais/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Master-Key': currentKey
      },
      body: JSON.stringify({ nome, url, email, senha, observacao: '' })
    });

    if (res.status === 401) {
      alert('Sua sessão expirou.');
      await chrome.storage.local.remove('pm_master_key');
      currentKey = null;
      showAuthScreen();
      return;
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Erro na API' }));
      throw new Error(err.detail || 'Erro ao adicionar.');
    }

    alert('Credencial salva com sucesso!');
    showMainScreen();
  } catch (e) {
    alert('Erro ao salvar credencial: ' + e.message);
  } finally {
    btnSaveCred.disabled = false;
    btnSaveCred.textContent = '💾 Salvar Credencial';
  }
});

// Navigation Helpers
function showAuthScreen() {
  screenAuth.classList.add('active');
  screenMain.classList.remove('active');
  screenAdd.classList.remove('active');
  inputKey.focus();
}

function showMainScreen() {
  screenAuth.classList.remove('active');
  screenMain.classList.add('active');
  screenAdd.classList.remove('active');
  inputSearch.value = '';
  loadCredentials();
}

async function showAddScreen() {
  screenAuth.classList.remove('active');
  screenMain.classList.remove('active');
  screenAdd.classList.add('active');

  // Reset values
  addNome.value = '';
  addUrl.value = '';
  addEmail.value = '';
  addSenha.value = '';

  if (activeTab) {
    try {
      const url = new URL(activeTab.url);
      addUrl.value = activeTab.url;
      addNome.value = url.hostname.replace(/^www\./, '');
      
      // Request active page inputs values from content script
      chrome.tabs.sendMessage(activeTab.id, { action: 'detect_credentials' }, (response) => {
        if (chrome.runtime.lastError || !response) return;
        if (response.user) addEmail.value = response.user;
        if (response.pass) addSenha.value = response.pass;
      });
    } catch {
      // Ignora falhas se URL for inválida (ex: chrome://)
    }
  }
}

// Fetch and Render credentials
async function loadCredentials(searchQuery = '') {
  let term = searchQuery;
  let isSuggestion = false;

  if (!term && activeTab) {
    try {
      const url = new URL(activeTab.url);
      term = url.hostname.replace(/^www\./, '');
      isSuggestion = true;
    } catch {
      term = '';
    }
  }

  suggestionsTitle.textContent = isSuggestion 
    ? `Sugestões para esta página (${term}):` 
    : 'Resultados da busca:';

  credContainer.innerHTML = '<div class="status-msg">Carregando...</div>';

  try {
    const endpoint = term 
      ? `${API_URL}/credenciais/buscar?termo=${encodeURIComponent(term)}`
      : `${API_URL}/credenciais/`;
      
    const res = await fetch(endpoint, {
      headers: { 'X-Master-Key': currentKey }
    });

    if (res.status === 401) {
      await chrome.storage.local.remove('pm_master_key');
      currentKey = null;
      showAuthScreen();
      return;
    }

    const creds = await res.json();
    renderCredentials(creds);
  } catch (e) {
    credContainer.innerHTML = '<div class="status-msg">Falha ao carregar credenciais. Verifique a conexão com o servidor local.</div>';
  }
}

function renderCredentials(creds) {
  if (!creds.length) {
    credContainer.innerHTML = '<div class="status-msg">Nenhuma credencial encontrada.</div>';
    return;
  }

  credContainer.innerHTML = '';
  creds.forEach(c => {
    const item = document.createElement('div');
    item.className = 'cred-item';
    item.innerHTML = `
      <div class="cred-name">${escapeHtml(c.nome)}</div>
      <div class="cred-email">${escapeHtml(c.email)}</div>
      <div class="cred-actions">
        <button class="action-badge" data-action="fill">Auto-Preencher</button>
        <button class="action-badge" data-action="copy-user">Copiar User</button>
        <button class="action-badge" data-action="copy-pass">Copiar Senha</button>
      </div>
    `;

    item.addEventListener('click', (e) => {
      const actionBtn = e.target.closest('.action-badge');
      if (!actionBtn) return;
      
      const action = actionBtn.dataset.action;
      if (action === 'fill') {
        fillCredentials(c.email, c.senha);
      } else if (action === 'copy-user') {
        copyToClipboard(c.email);
      } else if (action === 'copy-pass') {
        copyToClipboard(c.senha);
      }
    });

    credContainer.appendChild(item);
  });
}

async function fillCredentials(user, pass) {
  if (!activeTab) return;
  try {
    await chrome.tabs.sendMessage(activeTab.id, {
      action: 'fill_credentials',
      user: user,
      pass: pass
    });
    window.close();
  } catch (err) {
    alert('Erro ao preencher. Certifique-se de que a página está totalmente carregada.');
  }
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    alert('Copiado para a área de transferência!');
  });
}

function escapeHtml(str) {
  return String(str ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

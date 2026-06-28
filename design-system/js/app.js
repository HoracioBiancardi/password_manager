import { st } from './state.js';
import { toast, copyText, downloadBlob, initBackground, esc, initial } from './utils.js';
import { listar, adicionar, atualizar, remover, exportar, importar, resetVault } from './api.js';

const key = (c) => `${c.nome}::${c.email}`;

// ── Auth ───────────────────────────────────────────────────────────
function showLogin() {
  document.getElementById('login-overlay').classList.add('open');
  document.getElementById('topbar').style.display = 'none';
  document.getElementById('app-layout').style.display = 'none';
}

function showApp() {
  document.getElementById('login-overlay').classList.remove('open');
  document.getElementById('topbar').style.display = '';
  document.getElementById('app-layout').style.display = 'flex';
}

function onUnauthorized() {
  sessionStorage.removeItem('pm_key');
  st.masterKey = null;
  _hideDetail();
  _hideForm();
  showLogin();
  toast('Chave Mestre inválida ou expirada.', 'error');
}

export async function login() {
  const input = document.getElementById('master-key-input');
  const k = input.value.trim();
  if (!k) { toast('Digite a Chave Mestre.', 'warn'); return; }

  const btn = document.getElementById('login-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Verificando…';

  try {
    st.masterKey = k;
    await listar();
    sessionStorage.setItem('pm_key', k);
    st.freshKey = false;
    document.getElementById('new-vault-btn').style.display = 'none';
    showApp();
    await loadCredentials();
  } catch (e) {
    st.masterKey = null;
    if (e.status === 401) {
      if (st.freshKey) {
        toast('Chave nova não abre o cofre existente. Use "Criar Cofre Vazio" para apagar e recomeçar.', 'warn', 6000);
        document.getElementById('new-vault-btn').style.display = '';
      } else {
        toast('Chave inválida. Tente novamente.', 'error');
      }
    } else {
      toast(e.message, 'error');
    }
  } finally {
    btn.disabled = false;
    btn.textContent = '🔓 Desbloquear';
  }
}

export function logout() {
  sessionStorage.removeItem('pm_key');
  st.masterKey = null;
  st.freshKey = false;
  st.credentials = []; st.filtered = [];
  st.activeKey = null; st.activeCred = null;
  document.getElementById('new-vault-btn').style.display = 'none';
  _hideDetail();
  _hideForm();
  showLogin();
  document.getElementById('master-key-input').value = '';
  renderList();
}

export function toggleMasterVis() {
  const inp = document.getElementById('master-key-input');
  inp.type = inp.type === 'password' ? 'text' : 'password';
}

// ── Carregar credenciais ───────────────────────────────────────────
async function loadCredentials() {
  try {
    st.credentials = await listar();
    applyFilter();
    renderList();
    updateFooter();
  } catch (e) {
    if (e.status === 401) { onUnauthorized(); return; }
    toast('Erro ao carregar credenciais: ' + e.message, 'error');
  }
}

function applyFilter() {
  const q = st.searchQuery.toLowerCase();
  if (!q) { st.filtered = [...st.credentials]; return; }
  st.filtered = st.credentials.filter(c =>
    c.nome.toLowerCase().includes(q) ||
    c.email.toLowerCase().includes(q) ||
    (c.url || '').toLowerCase().includes(q)
  );
}

// ── Busca ──────────────────────────────────────────────────────────
export function onSearch(val) {
  st.searchQuery = val.trim();
  applyFilter();
  renderList();
}

// ── Helpers ────────────────────────────────────────────────────────
function domainOf(url) {
  try { return new URL(url).hostname.replace(/^www\./, ''); } catch { return ''; }
}

// ── Lista de credenciais ───────────────────────────────────────────
function renderList() {
  const el = document.getElementById('cred-list');
  const badge = document.getElementById('cred-count');

  if (!st.filtered.length) {
    el.innerHTML = `<div class="list-empty"><div class="ei">🔑</div>${
      st.searchQuery ? 'Nenhum resultado.' : 'Nenhuma credencial ainda.'
    }</div>`;
    badge.hidden = true;
    return;
  }

  badge.hidden = false;
  badge.textContent = st.filtered.length;

  el.innerHTML = st.filtered.map(c => {
    const dom = c.url ? domainOf(c.url) : '';
    const hasNote = Boolean(c.observacao && c.observacao.trim());
    return `
    <div class="vault-row${key(c) === st.activeKey ? ' active' : ''}"
         onclick="selectCred(${esc(JSON.stringify(key(c)))})"
         title="${esc(c.nome)}">
      <div class="vault-row-icon">${esc(initial(c.nome))}</div>
      <div class="vault-row-main">
        <div class="vault-row-name">${esc(c.nome)}</div>
        <div class="vault-row-email">${esc(c.email)}</div>
      </div>
      <div class="vault-row-domain">${dom ? `🔗 ${esc(dom)}` : ''}</div>
      <div class="vault-row-badges">${hasNote ? '<span title="Tem observação">📝</span>' : ''}</div>
      <div class="vault-row-actions">
        <button class="icon-btn del" title="Excluir"
          onclick="event.stopPropagation();openDeleteModal(${esc(JSON.stringify(key(c)))})">🗑</button>
      </div>
    </div>`;
  }).join('');
}

function updateFooter() {
  document.getElementById('sidebar-footer').textContent =
    `${st.credentials.length} credencial(is)`;
}

// ── Selecionar credencial ──────────────────────────────────────────
export function selectCred(k) {
  st.activeKey = k;
  st.activeCred = st.credentials.find(c => key(c) === k) || null;
  st.editing = false; st.isNew = false;
  renderList();
  if (st.activeCred) openDetailModal(st.activeCred);
}

// ── Detail modal ───────────────────────────────────────────────────
function openDetailModal(c) {
  document.getElementById('detail-title').textContent = c.nome;
  document.getElementById('detail-del-btn').onclick = () => openDeleteModal(key(c));
  document.getElementById('detail-fields').innerHTML = `
    ${fieldRow('🌐', 'URL', c.url, 'url', c.url)}
    ${fieldRow('📧', 'E-mail', c.email, 'email', c.email)}
    ${pwFieldRow(c.senha)}
    ${fieldRow('📝', 'Observação', c.observacao, 'obs')}
  `;
  document.getElementById('detail-overlay').classList.add('open');
}

function _hideDetail() {
  document.getElementById('detail-overlay').classList.remove('open');
}

export function closeDetailModal() {
  _hideDetail();
  st.activeKey = null; st.activeCred = null;
  renderList();
}

// ── Field rows (modo leitura) ──────────────────────────────────────
function fieldRow(icon, label, value, type = '', raw = '') {
  const empty = !value;
  const isUrl  = type === 'url' && value;
  const isObs  = type === 'obs';
  const valClass  = `field-row-value${isUrl ? ' url-link' : ''}${isObs ? ' obs' : ''}${empty ? ' empty' : ''}`;
  const valContent = empty ? '—' : esc(value);
  const urlClick   = isUrl ? `onclick="openUrl(${esc(JSON.stringify(value))})"` : '';
  const copyBtn    = !empty && !isObs
    ? `<button class="copy-btn" title="Copiar" onclick="doCopy(${esc(JSON.stringify(raw || value))}, this)">📋</button>`
    : '';
  return `
    <div class="field-row">
      <div class="field-row-icon">${icon}</div>
      <div class="field-row-body">
        <div class="field-row-label">${label}</div>
        <div class="${valClass}" ${urlClick}>${valContent}</div>
      </div>
      <div class="field-row-btns">${copyBtn}</div>
    </div>`;
}

function pwFieldRow(senha) {
  return `
    <div class="field-row">
      <div class="field-row-icon">🔑</div>
      <div class="field-row-body">
        <div class="field-row-label">Senha</div>
        <div class="field-row-value mono" id="pw-display">••••••••</div>
      </div>
      <div class="field-row-btns">
        <button class="copy-btn" title="Mostrar/ocultar"
          onclick="togglePwVis(${esc(JSON.stringify(senha))}, this)">👁</button>
        <button class="copy-btn" title="Copiar senha"
          onclick="doCopy(${esc(JSON.stringify(senha))}, this)">📋</button>
      </div>
    </div>`;
}

export function togglePwVis(senha, btn) {
  const el = document.getElementById('pw-display');
  if (el.dataset.visible === '1') {
    el.textContent = '••••••••'; el.dataset.visible = '0'; btn.textContent = '👁';
  } else {
    el.textContent = senha; el.dataset.visible = '1'; btn.textContent = '🙈';
  }
}

export function doCopy(text, btn) { copyText(text, btn); }
export function openUrl(url) { window.open(url, '_blank', 'noopener'); }

// ── Form modal ─────────────────────────────────────────────────────
function openFormModal(c) {
  document.getElementById('form-title-label').textContent = c ? 'Editar Credencial' : 'Nova Credencial';
  document.getElementById('f-nome').value    = c?.nome       ?? '';
  document.getElementById('f-url').value     = c?.url        ?? '';
  document.getElementById('f-email').value   = c?.email      ?? '';
  document.getElementById('f-senha').value   = c?.senha      ?? '';
  document.getElementById('f-obs').value     = c?.observacao ?? '';
  document.getElementById('form-overlay').classList.add('open');
  setTimeout(() => document.getElementById('f-nome').focus(), 50);
}

function _hideForm() {
  document.getElementById('form-overlay').classList.remove('open');
}

export function startEdit() {
  const c = st.activeCred;
  if (!c) return;
  st.editing = true; st.isNew = false;
  _hideDetail();
  openFormModal(c);
}

export function startNew() {
  st.activeKey = null; st.activeCred = null;
  st.editing = true; st.isNew = true;
  renderList();
  openFormModal(null);
}

export function cancelForm() {
  _hideForm();
  st.editing = false; st.isNew = false;
  if (st.activeCred) openDetailModal(st.activeCred);
}

export function toggleFormPwVis() {
  const inp = document.getElementById('f-senha');
  inp.type = inp.type === 'password' ? 'text' : 'password';
}

export async function saveForm() {
  const nome  = document.getElementById('f-nome').value.trim();
  const email = document.getElementById('f-email').value.trim();
  const senha = document.getElementById('f-senha').value.trim();
  const url   = document.getElementById('f-url').value.trim();
  const obs   = document.getElementById('f-obs').value.trim();

  if (!nome)  { toast('Nome do serviço é obrigatório.', 'warn'); return; }
  if (!email) { toast('E-mail é obrigatório.', 'warn'); return; }
  if (!senha) { toast('Senha é obrigatória.', 'warn'); return; }

  const btn = document.getElementById('save-btn');
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span>';

  try {
    if (st.isNew) {
      await adicionar({ nome, url, email, senha, observacao: obs });
      toast('Credencial adicionada!', 'success');
    } else {
      const prev = st.activeCred;
      await atualizar({
        nome_atual: prev.nome, email_atual: prev.email,
        nome, url, email, senha, observacao: obs,
      });
      toast('Credencial atualizada!', 'success');
    }
    st.editing = false; st.isNew = false;
    _hideForm();
    await loadCredentials();
    const nova = st.credentials.find(c => c.nome === nome && c.email === email);
    if (nova) { st.activeKey = key(nova); st.activeCred = nova; renderList(); openDetailModal(nova); }
  } catch (e) {
    if (e.status === 401) { onUnauthorized(); return; }
    toast('Erro ao salvar: ' + e.message, 'error');
  } finally {
    btn.disabled = false; btn.textContent = '💾 Salvar';
  }
}

// ── Gerar chave Fernet ─────────────────────────────────────────────
let _generatedKey = null;

function _makeFernetKey() {
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  return btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_');
}

export function openKeyGenModal() {
  _generatedKey = _makeFernetKey();
  document.getElementById('keygen-key-text').textContent = _generatedKey;
  document.getElementById('keygen-overlay').classList.add('open');
}

export function closeKeyGenModal() {
  document.getElementById('keygen-overlay').classList.remove('open');
}

export function regenerateKey() {
  _generatedKey = _makeFernetKey();
  document.getElementById('keygen-key-text').textContent = _generatedKey;
  const btn = document.getElementById('keygen-copy-btn');
  btn.classList.remove('copied');
  btn.textContent = '📋';
}

export function copyGeneratedKey(btn) {
  copyText(_generatedKey, btn);
}

export function useGeneratedKey() {
  document.getElementById('master-key-input').value = _generatedKey;
  st.freshKey = true;
  closeKeyGenModal();
  toast('Chave aplicada no campo. Guarde-a antes de continuar!', 'warn', 5000);
  document.getElementById('master-key-input').focus();
}

// ── Criar cofre vazio com nova chave ──────────────────────────────
export async function createNewVault() {
  if (!confirm('Isso vai APAGAR permanentemente todas as senhas do cofre atual. Confirmar?')) return;
  const k = document.getElementById('master-key-input').value.trim();
  if (!k) { toast('Digite a Chave Mestre no campo.', 'warn'); return; }
  try {
    st.masterKey = k;
    await resetVault();
    toast('Cofre apagado. Fazendo login com a nova chave…', 'info', 3000);
    document.getElementById('new-vault-btn').style.display = 'none';
    st.freshKey = false;
    await login();
  } catch (e) {
    st.masterKey = null;
    toast('Erro ao apagar cofre: ' + e.message, 'error');
  }
}

// ── Delete modal ───────────────────────────────────────────────────
export function openDeleteModal(k) {
  st.pendingDelete = k;
  const c = st.credentials.find(c => key(c) === k);
  document.getElementById('del-name').textContent = c?.nome ?? k;
  document.getElementById('delete-overlay').classList.add('open');
}

export function closeDeleteModal() {
  document.getElementById('delete-overlay').classList.remove('open');
  st.pendingDelete = null;
}

export async function confirmDelete() {
  if (!st.pendingDelete) return;
  const [nome, email] = st.pendingDelete.split('::');
  const btn = document.getElementById('confirm-del-btn');
  btn.disabled = true; btn.innerHTML = '<span class="spinner"></span>';

  try {
    await remover(nome, email);
    closeDeleteModal();
    _hideDetail();
    toast('Credencial removida.', 'success');
    st.activeKey = null; st.activeCred = null;
    await loadCredentials();
  } catch (e) {
    if (e.status === 401) { onUnauthorized(); return; }
    toast('Erro ao remover: ' + e.message, 'error');
    closeDeleteModal();
  } finally {
    btn.disabled = false; btn.textContent = 'Excluir';
  }
}

// ── Exportar ───────────────────────────────────────────────────────
export async function doExport() {
  try {
    const { blob, filename } = await exportar();
    downloadBlob(blob, filename);
    toast('Backup exportado!', 'success');
  } catch (e) {
    if (e.status === 401) { onUnauthorized(); return; }
    toast('Erro ao exportar: ' + e.message, 'error');
  }
}

// ── Importar ───────────────────────────────────────────────────────
export function doImport() {
  document.getElementById('import-input').click();
}

export async function onImportFile(input) {
  const file = input.files[0];
  if (!file) return;
  input.value = '';

  let payload;
  try {
    payload = JSON.parse(await file.text());
  } catch {
    toast('Arquivo inválido: não é um JSON válido.', 'error');
    return;
  }

  try {
    const result = await importar(payload);
    const msg = `${result.senhas_importadas} senha(s) importada(s)` +
      (result.senhas_ignoradas ? `, ${result.senhas_ignoradas} já existiam.` : '.');
    toast(msg, 'success', 4000);
    await loadCredentials();
  } catch (e) {
    if (e.status === 401) { onUnauthorized(); return; }
    toast('Erro ao importar: ' + e.message, 'error');
  }
}

// ── Conexão ────────────────────────────────────────────────────────
async function checkConn() {
  try {
    await fetch('/health');
    const b = document.getElementById('conn-badge');
    b.textContent = '● online'; b.classList.add('online');
  } catch {
    document.getElementById('conn-badge').textContent = '● offline';
  }
}

// ── Expor ao DOM ───────────────────────────────────────────────────
Object.assign(window, {
  login, logout, toggleMasterVis,
  onSearch,
  selectCred,
  startEdit, startNew, cancelForm, saveForm, toggleFormPwVis,
  togglePwVis, doCopy, openUrl,
  closeDetailModal,
  openDeleteModal, closeDeleteModal, confirmDelete,
  doExport,
  openKeyGenModal, closeKeyGenModal, regenerateKey, copyGeneratedKey, useGeneratedKey,
  createNewVault,
  doImport, onImportFile,
});

// ── Init ───────────────────────────────────────────────────────────
(async () => {
  initBackground();
  await checkConn();
  if (st.masterKey) {
    try {
      showApp();
      await loadCredentials();
    } catch {
      showLogin();
    }
  } else {
    showLogin();
  }
})();

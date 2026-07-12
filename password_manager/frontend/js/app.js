import { st } from './state.js';
import { toast, copyText, downloadBlob, initBackground, esc, initial, passwordStrength, timeAgo, parseCsv } from './utils.js';
import { listar, adicionar, atualizar, remover, exportar, importar, importarCriptografado, resetVault } from './api.js';
import { applyPrefsOnBoot, getCrtScanlines, getCrtFlicker, getCrtTheme, getCrtStatic, getCrtCurved, setCrtScanlines, setCrtFlicker, setCrtTheme, setCrtStatic, setCrtCurved, getAutoLockMinutes, setAutoLockMinutes } from './prefs.js';

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
    
    const remember = document.getElementById('remember-key-checkbox').checked;
    if (remember) {
      localStorage.setItem('pm_key', k);
      sessionStorage.removeItem('pm_key');
    } else {
      sessionStorage.setItem('pm_key', k);
      localStorage.removeItem('pm_key');
    }

    st.freshKey = false;
    document.getElementById('new-vault-btn').style.display = 'none';
    showApp();
    await loadCredentials();
    resetLockTimer();
  } catch (e) {
    st.masterKey = null;
    if (e.status === 401) {
      toast('Senha incorreta para o cofre existente. Para redefinir usando esta senha, clique em "Criar cofre vazio" (atenção: apaga os dados atuais).', 'warn', 7000);
      document.getElementById('new-vault-btn').style.display = '';
    } else {
      toast(e.message, 'error');
    }
  } finally {
    btn.disabled = false;
    btn.textContent = '🔓 Desbloquear';
  }
}

export function logout() {
  clearTimeout(_lockTimer);
  sessionStorage.removeItem('pm_key');
  localStorage.removeItem('pm_key');
  st.masterKey = null;
  st.freshKey = false;
  st.credentials = []; st.filtered = [];
  st.activeKey = null; st.activeCred = null;
  document.getElementById('new-vault-btn').style.display = 'none';
  _hideDetail();
  _hideForm();
  showLogin();
  document.getElementById('master-key-input').value = '';
  document.getElementById('remember-key-checkbox').checked = false;
  renderList();
}

export function toggleMasterVis() {
  const inp = document.getElementById('master-key-input');
  inp.type = inp.type === 'password' ? 'text' : 'password';
}

// ── Bloqueio automático por inatividade ──────────────────────────────
let _lockTimer = null;

function resetLockTimer() {
  clearTimeout(_lockTimer);
  if (!st.masterKey) return;
  const minutes = getAutoLockMinutes();
  if (!minutes) return;
  _lockTimer = setTimeout(lockVault, minutes * 60 * 1000);
}

function lockVault() {
  if (!st.masterKey) return;
  st.masterKey = null;
  st.credentials = []; st.filtered = [];
  st.activeKey = null; st.activeCred = null;
  _hideDetail();
  _hideForm();
  showLogin();
  document.getElementById('master-key-input').value = '';
  renderList();
  toast('Cofre bloqueado por inatividade.', 'warn', 4000);
}

export function changeAutoLock(val) {
  setAutoLockMinutes(Number(val));
  resetLockTimer();
}

['mousemove', 'keydown', 'mousedown', 'scroll', 'touchstart'].forEach(evt =>
  document.addEventListener(evt, resetLockTimer, { passive: true })
);

// ── Carregar credenciais ───────────────────────────────────────────
async function loadCredentials() {
  try {
    st.credentials = await listar();
    updateDupBadge();
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
  let base = !q ? st.credentials : st.credentials.filter(c =>
    c.nome.toLowerCase().includes(q) ||
    c.email.toLowerCase().includes(q) ||
    (c.url || '').toLowerCase().includes(q)
  );
  if (st.showDuplicatesOnly) {
    const counts = passwordCounts();
    base = base.filter(c => c.senha && counts.get(c.senha) > 1);
  }
  st.filtered = sortCreds(base);
}

// ── Senhas reutilizadas ──────────────────────────────────────────────
function passwordCounts() {
  const counts = new Map();
  for (const c of st.credentials) {
    if (!c.senha) continue;
    counts.set(c.senha, (counts.get(c.senha) || 0) + 1);
  }
  return counts;
}

function updateDupBadge() {
  const counts = passwordCounts();
  const dupCount = st.credentials.filter(c => c.senha && counts.get(c.senha) > 1).length;
  const btn = document.getElementById('dup-toggle-btn');
  if (!dupCount) {
    btn.hidden = true;
    st.showDuplicatesOnly = false;
    return;
  }
  btn.hidden = false;
  btn.textContent = `♻️ ${dupCount}`;
  btn.title = st.showDuplicatesOnly
    ? 'Mostrando apenas senhas reutilizadas — clique para ver todas'
    : `${dupCount} senha(s) reutilizada(s) em mais de uma conta — clique para filtrar`;
  btn.classList.toggle('btn-primary', st.showDuplicatesOnly);
  btn.classList.toggle('btn-ghost', !st.showDuplicatesOnly);
}

export function toggleDuplicatesFilter() {
  st.showDuplicatesOnly = !st.showDuplicatesOnly;
  applyFilter();
  renderList();
  updateDupBadge();
}

// ── Ordenação ──────────────────────────────────────────────────────
function sortCreds(list) {
  const dir = st.sortDir === 'desc' ? -1 : 1;
  return [...list].sort((a, b) => {
    let va, vb;
    if (st.sortKey === 'atualizado') { va = a.atualizado_em || ''; vb = b.atualizado_em || ''; }
    else if (st.sortKey === 'dominio') { va = domainOf(a.url || ''); vb = domainOf(b.url || ''); }
    else { va = a.nome.toLowerCase(); vb = b.nome.toLowerCase(); }
    if (va < vb) return -1 * dir;
    if (va > vb) return 1 * dir;
    return 0;
  });
}

export function onSortChange(val) {
  const [sortKey, sortDir] = val.split('-');
  st.sortKey = sortKey; st.sortDir = sortDir;
  applyFilter();
  renderList();
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
    const msg = st.searchQuery
      ? 'Nenhum resultado.'
      : (st.showDuplicatesOnly ? 'Nenhuma senha duplicada. 🎉' : 'Nenhuma credencial ainda.');
    el.innerHTML = `<div class="list-empty"><div class="ei">🔑</div>${msg}</div>`;
    badge.hidden = true;
    return;
  }

  badge.hidden = false;
  badge.textContent = st.filtered.length;

  const counts = passwordCounts();

  el.innerHTML = st.filtered.map(c => {
    const dom = c.url ? domainOf(c.url) : '';
    const hasNote = Boolean(c.observacao && c.observacao.trim());
    const isDup = Boolean(c.senha && counts.get(c.senha) > 1);
    const strength = passwordStrength(c.senha);
    const updated = timeAgo(c.atualizado_em);
    return `
    <div class="vault-row${key(c) === st.activeKey ? ' active' : ''}"
         onclick="selectCred(${esc(JSON.stringify(key(c)))})"
         title="${esc(c.nome)}">
      <div class="vault-row-icon">${esc(initial(c.nome))}</div>
      <div class="vault-row-main">
        <div class="vault-row-name">${esc(c.nome)}</div>
        <div class="vault-row-email">${esc(c.email)}</div>
      </div>
      <div class="vault-row-meta">
        <div class="vault-row-meta-top">
          ${dom ? `<span class="vault-row-domain">🔗 ${esc(dom)}</span>` : ''}
          ${isDup ? '<span title="Senha reutilizada em outra conta">♻️</span>' : ''}
          ${hasNote ? '<span title="Tem observação">📝</span>' : ''}
        </div>
        <div class="vault-row-meta-bottom">
          <span class="pw-strength-dot ${strength.cls}" title="Força da senha: ${strength.label}"></span>
          <span class="vault-row-updated" title="Última atualização">${esc(updated)}</span>
        </div>
      </div>
      <div class="vault-row-actions">
        ${c.url ? `<button class="icon-btn" title="Abrir URL" onclick="event.stopPropagation();openUrl(${esc(JSON.stringify(c.url))})">🌐</button>` : ''}
        <button class="icon-btn" title="Copiar e-mail"
          onclick="event.stopPropagation();doCopy(${esc(JSON.stringify(c.email))}, this)">📧</button>
        <button class="icon-btn" title="Copiar senha"
          onclick="event.stopPropagation();doCopy(${esc(JSON.stringify(c.senha))}, this)">🔑</button>
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
  const metaEl = document.getElementById('detail-meta');
  const criado = c.criado_em ? `Criada ${timeAgo(c.criado_em)}` : 'Data de criação desconhecida';
  const atualizado = c.atualizado_em && c.atualizado_em !== c.criado_em ? ` · Atualizada ${timeAgo(c.atualizado_em)}` : '';
  metaEl.textContent = criado + atualizado;
  document.getElementById('detail-del-btn').onclick = () => openDeleteModal(key(c));
  const isDup = Boolean(c.senha && passwordCounts().get(c.senha) > 1);
  document.getElementById('detail-fields').innerHTML = `
    ${fieldRow('🌐', 'URL', c.url, 'url', c.url)}
    ${fieldRow('📧', 'E-mail', c.email, 'email', c.email)}
    ${pwFieldRow(c.senha, isDup)}
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

function pwFieldRow(senha, isDup = false) {
  const strength = passwordStrength(senha);
  const dupTag = isDup
    ? ' <span class="pw-strength-tag pw-dup" title="Esta senha também é usada em outra conta">♻ Reutilizada</span>'
    : '';
  return `
    <div class="field-row">
      <div class="field-row-icon">🔑</div>
      <div class="field-row-body">
        <div class="field-row-label">Senha <span class="pw-strength-tag ${strength.cls}">${strength.label}</span>${dupTag}</div>
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
    const { blob, filename } = await exportar(false);
    downloadBlob(blob, filename);
    toast('Backup exportado!', 'success');
  } catch (e) {
    if (e.status === 401) { onUnauthorized(); return; }
    toast('Erro ao exportar: ' + e.message, 'error');
  }
}

export async function doExportEncrypted() {
  try {
    const { blob, filename } = await exportar(true);
    downloadBlob(blob, filename);
    toast('Backup criptografado exportado! A mesma Chave Mestre é necessária para reimportá-lo.', 'success', 5000);
  } catch (e) {
    if (e.status === 401) { onUnauthorized(); return; }
    toast('Erro ao exportar: ' + e.message, 'error');
  }
}

// ── Importar ───────────────────────────────────────────────────────
export function doImport() {
  document.getElementById('import-input').click();
}

// Converte um CSV exportado do Chrome/Edge/Brave ou Firefox para o
// formato de importação da API ({ version, senhas: [...] }).
function csvToImportPayload(text) {
  const rows = parseCsv(text).filter(r => r.length && r.some(v => v.trim() !== ''));
  if (!rows.length) throw new Error('arquivo CSV vazio.');

  const header = rows[0].map(h => h.trim().toLowerCase());
  const idx = (...names) => {
    for (const n of names) {
      const i = header.indexOf(n);
      if (i !== -1) return i;
    }
    return -1;
  };

  const iName = idx('name');
  const iUrl  = idx('url', 'login_uri');
  const iUser = idx('username', 'login_username');
  const iPass = idx('password', 'login_password');
  const iNote = idx('note', 'notes', 'extra');

  if (iUser === -1 || iPass === -1) {
    throw new Error('formato não reconhecido (esperado export do Chrome/Edge ou Firefox).');
  }

  const senhas = rows.slice(1).map(r => {
    const url = (r[iUrl] ?? '').trim();
    let nome = (iName !== -1 ? r[iName] : '').trim();
    if (!nome) {
      try { nome = new URL(url).hostname.replace(/^www\./, ''); } catch { nome = url || 'Sem nome'; }
    }
    return {
      nome,
      url,
      email: (r[iUser] ?? '').trim(),
      senha: (r[iPass] ?? '').trim(),
      observacao: iNote !== -1 ? (r[iNote] ?? '').trim() : '',
    };
  }).filter(c => c.email || c.senha);

  return { version: 1, senhas };
}

export async function onImportFile(input) {
  const file = input.files[0];
  if (!file) return;
  input.value = '';

  const name = file.name.toLowerCase();
  const isCsv = name.endsWith('.csv');
  const isEnc = name.endsWith('.enc');

  let result;
  try {
    if (isEnc) {
      result = await importarCriptografado(await file.arrayBuffer());
    } else {
      const text = await file.text();
      const payload = isCsv ? csvToImportPayload(text) : JSON.parse(text);
      result = await importar(payload);
    }
  } catch (e) {
    if (e.status === 401) { onUnauthorized(); return; }
    if (isEnc) toast('Backup criptografado inválido ou Chave Mestre incorreta: ' + e.message, 'error');
    else if (isCsv) toast('CSV inválido: ' + e.message, 'error');
    else toast('Arquivo inválido: não é um JSON válido.', 'error');
    return;
  }

  const msg = `${result.senhas_importadas} senha(s) importada(s)` +
    (result.senhas_ignoradas ? `, ${result.senhas_ignoradas} já existiam.` : '.');
  toast(msg, 'success', 4000);
  await loadCredentials();
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

// ── Settings Modal Tabs & Bookmarklet ──────────────────────────────
const SETTINGS_TABS = ['appearance', 'security', 'integration'];

export function switchSettingsTab(tab) {
  for (const t of SETTINGS_TABS) {
    document.getElementById(`tab-btn-${t}`).classList.toggle('active', t === tab);
    document.getElementById(`tab-content-${t}`).style.display =
      t === tab ? (t === 'integration' ? 'flex' : 'block') : 'none';
  }
}

export function openSettingsModal() {
  document.getElementById('settings-overlay').classList.add('open');
  document.getElementById('settings-scanlines').checked = getCrtScanlines();
  document.getElementById('settings-flicker').checked = getCrtFlicker();
  document.getElementById('settings-static').checked = getCrtStatic();
  document.getElementById('settings-curved').checked = getCrtCurved();
  document.getElementById('settings-theme').value = getCrtTheme();
  document.getElementById('settings-autolock').value = String(getAutoLockMinutes());
  switchSettingsTab('appearance');
}

export function closeSettingsModal() {
  document.getElementById('settings-overlay').classList.remove('open');
}

function initBookmarklet() {
  const code = `javascript:(async function(){
    const existing = document.getElementById('pm-vault-bookmarklet');
    if (existing) { existing.remove(); return; }

    const style = document.createElement('style');
    style.id = 'pm-vault-style';
    style.textContent = \`
      #pm-vault-bookmarklet {
        position: fixed; top: 15px; right: 15px; width: 320px;
        background: #061107; border: 2px solid #1aff80; border-radius: 4px;
        color: #1aff80; font-family: 'Share Tech Mono', monospace; z-index: 999999;
        box-shadow: 0 4px 20px rgba(0,0,0,0.8), 0 0 10px rgba(26,255,128,0.3);
        padding: 12px; font-size: 13px; text-shadow: 0 0 4px rgba(26,255,128,0.5);
      }
      #pm-vault-bookmarklet h3 { margin: 0 0 10px 0; font-size: 14px; font-weight: bold; border-bottom: 1px solid rgba(26,255,128,0.3); padding-bottom: 5px; display:flex; justify-content:space-between; }
      #pm-vault-bookmarklet input {
        width: 100%; background: #0b220e; border: 1px solid rgba(26,255,128,0.4);
        color: #1aff80; padding: 4px 8px; margin-bottom: 8px; font-family: inherit; font-size: 12px;
        box-sizing: border-box; outline: none;
      }
      #pm-vault-bookmarklet button {
        background: #1aff80; color: #030804; border: none; padding: 4px 8px;
        cursor: pointer; font-family: inherit; font-size: 12px; font-weight: bold; width: 100%; margin-top: 4px;
      }
      #pm-vault-bookmarklet .cred-item {
        padding: 6px; border: 1px solid rgba(26,255,128,0.2); margin-top: 6px; cursor: pointer;
        background: #0b220e; border-radius: 2px; transition: all 0.2s;
      }
      #pm-vault-bookmarklet .cred-item:hover { background: #113315; border-color: #1aff80; }
    \`;
    document.head.appendChild(style);

    const div = document.createElement('div');
    div.id = 'pm-vault-bookmarklet';
    div.innerHTML = \`
      <h3>PM Vault <span>[X]</span></h3>
      <div id="pm-setup">
        <input type="password" id="pm-key-in" placeholder="Chave Mestre Fernet...">
        <button id="pm-btn-load">Buscar Credenciais</button>
      </div>
      <div id="pm-main-panel" style="display:none; flex-direction:column;">
        <div style="display:flex; gap:4px; margin-bottom:8px">
          <button id="pm-btn-reload" style="flex:1">🔄 Recarregar</button>
          <button id="pm-btn-add-show" style="flex:1">➕ Salvar Página</button>
        </div>
        <div id="pm-results" style="max-height: 180px; overflow-y: auto;"></div>
        <div id="pm-add-panel" style="display:none; flex-direction:column; gap:6px; margin-top:8px; border-top:1px solid rgba(26,255,128,0.2); padding-top:8px;">
          <input type="text" id="pm-add-name" placeholder="Serviço / Nome *">
          <input type="text" id="pm-add-url" placeholder="URL">
          <input type="text" id="pm-add-email" placeholder="E-mail / User *">
          <input type="password" id="pm-add-pass" placeholder="Senha *">
          <button id="pm-btn-add-submit">Confirmar Salvar</button>
        </div>
      </div>
    \`;
    document.body.appendChild(div);

    div.querySelector('h3 span').onclick = () => { div.remove(); style.remove(); };

    let currentMasterKey = sessionStorage.getItem('pm_vault_key');
    if (currentMasterKey) {
      div.querySelector('#pm-key-in').value = currentMasterKey;
    }

    const loadCreds = async () => {
      const k = div.querySelector('#pm-key-in').value.trim();
      if (!k) return;
      sessionStorage.setItem('pm_vault_key', k);
      currentMasterKey = k;

      const term = window.location.hostname.replace(/^www\\./, '');
      const resDiv = div.querySelector('#pm-results');
      resDiv.innerHTML = 'Buscando...';

      try {
        const r = await fetch('${window.location.origin}/api/credenciais/buscar?termo=' + encodeURIComponent(term), {
          headers: { 'X-Master-Key': k }
        });
        if (r.status === 401) { resDiv.innerHTML = 'Chave Mestre inválida.'; return; }
        if (!r.ok) { resDiv.innerHTML = 'Erro na API.'; return; }
        const creds = await r.json();

        div.querySelector('#pm-setup').style.display = 'none';
        div.querySelector('#pm-main-panel').style.display = 'flex';

        if (!creds.length) {
          resDiv.innerHTML = '<div style="text-align:center;padding:10px;opacity:0.8">Nenhuma credencial sugerida para ' + term + '</div>';
          return;
        }

        resDiv.innerHTML = '';
        creds.forEach(c => {
          const item = document.createElement('div');
          item.className = 'cred-item';
          item.innerHTML = '<strong>' + c.nome + '</strong><br><span style="font-size:10px; opacity:0.7">' + c.email + '</span>';
          item.onclick = () => {
            const pwFields = document.querySelectorAll('input[type="password"]');
            if (pwFields.length) {
              pwFields.forEach(pf => {
                pf.value = c.senha;
                pf.dispatchEvent(new Event('input', { bubbles: true }));
                pf.dispatchEvent(new Event('change', { bubbles: true }));
              });
              const userFields = document.querySelectorAll('input[type="email"], input[type="text"], input:not([type])');
              if (userFields.length) {
                let filled = false;
                for(let i = 0; i < userFields.length; i++) {
                  if (userFields[i].getBoundingClientRect().top < pwFields[0].getBoundingClientRect().top) {
                    userFields[i].value = c.email;
                    userFields[i].dispatchEvent(new Event('input', { bubbles: true }));
                    userFields[i].dispatchEvent(new Event('change', { bubbles: true }));
                    filled = true;
                  }
                }
                if (!filled) {
                  userFields[0].value = c.email;
                  userFields[0].dispatchEvent(new Event('input', { bubbles: true }));
                  userFields[0].dispatchEvent(new Event('change', { bubbles: true }));
                }
              }
            }
            div.remove(); style.remove();
          };
          resDiv.appendChild(item);
        });
      } catch (e) {
        resDiv.innerHTML = 'Erro ao conectar no cofre local.';
      }
    };

    const detectFields = () => {
      const passwordInputs = document.querySelectorAll('input[type="password"]');
      let passVal = '';
      let userVal = '';

      const pwInput = Array.from(passwordInputs).find(input => input.value.trim()) || passwordInputs[0];
      if (pwInput) {
        passVal = pwInput.value;
        const allInputs = Array.from(document.querySelectorAll('input'));
        const pwIndex = allInputs.indexOf(pwInput);
        if (pwIndex !== -1) {
          let usernameInput = null;
          for (let i = pwIndex - 1; i >= 0; i--) {
            const input = allInputs[i];
            const type = input.type.toLowerCase();
            if ((type === 'text' || type === 'email' || type === 'tel' || !input.hasAttribute('type')) && 
                input.offsetWidth > 0 && input.offsetHeight > 0) {
              usernameInput = input;
              break;
            }
          }
          if (!usernameInput) {
            usernameInput = Array.from(document.querySelectorAll('input[type="email"], input[type="text"]')).find(input => input.value.trim()) ||
                            document.querySelector('input[type="email"], input[type="text"]');
          }
          if (usernameInput) {
            userVal = usernameInput.value;
          }
        }
      }
      return { user: userVal, pass: passVal };
    };

    div.querySelector('#pm-btn-load').onclick = loadCreds;
    div.querySelector('#pm-key-in').onkeydown = (e) => { if(e.key === 'Enter') loadCreds(); };
    div.querySelector('#pm-btn-reload').onclick = loadCreds;
    
    const addPanel = div.querySelector('#pm-add-panel');
    div.querySelector('#pm-btn-add-show').onclick = () => {
      if (addPanel.style.display === 'none') {
        addPanel.style.display = 'flex';
        div.querySelector('#pm-add-name').value = window.location.hostname.replace(/^www\\./, '');
        div.querySelector('#pm-add-url').value = window.location.href;
        
        const detected = detectFields();
        div.querySelector('#pm-add-email').value = detected.user;
        div.querySelector('#pm-add-pass').value = detected.pass;
      } else {
        addPanel.style.display = 'none';
      }
    };

    div.querySelector('#pm-btn-add-submit').onclick = async () => {
      const nome = div.querySelector('#pm-add-name').value.trim();
      const url = div.querySelector('#pm-add-url').value.trim();
      const email = div.querySelector('#pm-add-email').value.trim();
      const senha = div.querySelector('#pm-add-pass').value.trim();

      if (!nome || !email || !senha) {
        alert('Os campos Nome, E-mail/Usuário e Senha são obrigatórios.');
        return;
      }

      try {
        const r = await fetch('${window.location.origin}/api/credenciais/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Master-Key': currentMasterKey
          },
          body: JSON.stringify({ nome, url, email, senha, observacao: '' })
        });

        if (!r.ok) throw new Error('Falha ao salvar.');
        alert('Salvo com sucesso!');
        addPanel.style.display = 'none';
        loadCreds();
      } catch(err) {
        alert('Erro ao salvar: ' + err.message);
      }
    };

    if (currentMasterKey) loadCreds();
  })()`;

  const compressed = code.replace(/\s+/g, ' ');
  const link = document.getElementById('bookmarklet-link');
  if (link) {
    link.href = compressed;
  }
}

// ── Expor ao DOM ───────────────────────────────────────────────────
Object.assign(window, {
  login, logout, toggleMasterVis,
  onSearch, onSortChange, toggleDuplicatesFilter,
  selectCred,
  startEdit, startNew, cancelForm, saveForm, toggleFormPwVis,
  togglePwVis, doCopy, openUrl,
  closeDetailModal,
  openDeleteModal, closeDeleteModal, confirmDelete,
  doExport, doExportEncrypted,
  openKeyGenModal, closeKeyGenModal, regenerateKey, copyGeneratedKey, useGeneratedKey,
  createNewVault,
  doImport, onImportFile,
  openSettingsModal, closeSettingsModal,
  toggleScanlines: setCrtScanlines,
  toggleFlicker: setCrtFlicker,
  toggleStatic: setCrtStatic,
  toggleCurved: setCrtCurved,
  changeTheme: setCrtTheme,
  changeAutoLock,
  switchSettingsTab,
});

// ── Init ───────────────────────────────────────────────────────────
(async () => {
  applyPrefsOnBoot();
  initBackground();
  initBookmarklet();
  await checkConn();
  if (st.masterKey) {
    try {
      showApp();
      await loadCredentials();
      resetLockTimer();
    } catch {
      showLogin();
    }
  } else {
    showLogin();
  }
})();

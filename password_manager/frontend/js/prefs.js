// Responsabilidade: preferências visuais do Pip-Boy CRT persistidas no navegador

const SCANLINES_KEY = 'pm-crt-scanlines';
const FLICKER_KEY = 'pm-crt-flicker';
const THEME_KEY = 'pm-crt-theme';
const STATIC_KEY = 'pm-crt-static';
const CURVED_KEY = 'pm-crt-curved';

export function getCrtScanlines() {
  const saved = localStorage.getItem(SCANLINES_KEY);
  return saved === null ? true : saved === 'true';
}

export function setCrtScanlines(enabled) {
  localStorage.setItem(SCANLINES_KEY, String(enabled));
  document.body.classList.toggle('crt-enabled', enabled);
  const el = document.getElementById('settings-scanlines');
  if (el) el.checked = enabled;
}

export function getCrtFlicker() {
  const saved = localStorage.getItem(FLICKER_KEY);
  return saved === null ? true : saved === 'true';
}

export function setCrtFlicker(enabled) {
  localStorage.setItem(FLICKER_KEY, String(enabled));
  document.body.classList.toggle('flicker-enabled', enabled);
  const el = document.getElementById('settings-flicker');
  if (el) el.checked = enabled;
}

export function getCrtStatic() {
  const saved = localStorage.getItem(STATIC_KEY);
  return saved === null ? false : saved === 'true'; // Padrão desativado
}

export function setCrtStatic(enabled) {
  localStorage.setItem(STATIC_KEY, String(enabled));
  document.body.classList.toggle('static-enabled', enabled);
  const el = document.getElementById('settings-static');
  if (el) el.checked = enabled;
}

export function getCrtCurved() {
  const saved = localStorage.getItem(CURVED_KEY);
  return saved === null ? true : saved === 'true'; // Padrão ativado
}

export function setCrtCurved(enabled) {
  localStorage.setItem(CURVED_KEY, String(enabled));
  document.body.classList.toggle('curved-enabled', enabled);
  const el = document.getElementById('settings-curved');
  if (el) el.checked = enabled;
}

export function getCrtTheme() {
  const saved = localStorage.getItem(THEME_KEY);
  return saved || 'green';
}

export function setCrtTheme(theme) {
  localStorage.setItem(THEME_KEY, theme);
  document.body.classList.remove('theme-green', 'theme-amber', 'theme-blue', 'theme-white');
  document.body.classList.add('theme-' + theme);
  const el = document.getElementById('settings-theme');
  if (el) el.value = theme;
}

export function openSettingsModal() {
  document.getElementById('settings-overlay').classList.add('open');
  document.getElementById('settings-scanlines').checked = getCrtScanlines();
  document.getElementById('settings-flicker').checked = getCrtFlicker();
  document.getElementById('settings-static').checked = getCrtStatic();
  document.getElementById('settings-curved').checked = getCrtCurved();
  document.getElementById('settings-theme').value = getCrtTheme();
}

export function closeSettingsModal() {
  document.getElementById('settings-overlay').classList.remove('open');
}

// Aplica as preferências salvas no boot
export function applyPrefsOnBoot() {
  setCrtScanlines(getCrtScanlines());
  setCrtFlicker(getCrtFlicker());
  setCrtStatic(getCrtStatic());
  setCrtCurved(getCrtCurved());
  setCrtTheme(getCrtTheme());
}

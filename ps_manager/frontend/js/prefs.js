// Responsabilidade: preferências visuais e de segurança persistidas no navegador

const THEME_KEY = 'pm-theme';
const AUTOLOCK_KEY = 'pm-autolock-minutes';
const EXPIRING_DAYS_KEY = 'pm-expiring-alert-days';

const VALID_THEMES = new Set([
  'corporate',
  'green-neutral',
  'cyber-dark'
]);


export function getCrtTheme() {
  const saved = localStorage.getItem(THEME_KEY);
  return VALID_THEMES.has(saved) ? saved : 'corporate';
}

export function setCrtTheme(theme) {
  const validTheme = VALID_THEMES.has(theme) ? theme : 'corporate';
  localStorage.setItem(THEME_KEY, validTheme);
  VALID_THEMES.forEach((t) => document.body.classList.remove('theme-' + t));
  document.body.classList.add('theme-' + validTheme);
  const el = document.getElementById('settings-theme');
  if (el) el.value = validTheme;
}

// ── Bloqueio automático por inatividade ─────────────────────────────
export function getAutoLockMinutes() {
  const saved = localStorage.getItem(AUTOLOCK_KEY);
  return saved === null ? 5 : Number(saved); // padrão: 5 minutos
}

export function setAutoLockMinutes(minutes) {
  localStorage.setItem(AUTOLOCK_KEY, String(minutes));
  const el = document.getElementById('settings-autolock');
  if (el) el.value = String(minutes);
}

// ── Alerta de expiração de credenciais ──────────────────────────────
export function getExpiringAlertDays() {
  const saved = localStorage.getItem(EXPIRING_DAYS_KEY);
  return saved === null ? 30 : Number(saved); // padrão: 30 dias
}

export function setExpiringAlertDays(days) {
  localStorage.setItem(EXPIRING_DAYS_KEY, String(days));
  const el = document.getElementById('settings-expiring-days');
  if (el) el.value = String(days);
}

// Aplica as preferências salvas no boot
export function applyPrefsOnBoot() {
  setCrtTheme(getCrtTheme());
}

// Fallback lê o nome antigo da chave (pm_key) para não deslogar quem já tinha
// "lembrar chave" marcado antes do rename para pm_chave_mestre.
const _chaveArmazenada =
  localStorage.getItem('pm_chave_mestre') || sessionStorage.getItem('pm_chave_mestre') ||
  localStorage.getItem('pm_key') || sessionStorage.getItem('pm_key') || null;

export const st = {
  masterKey: _chaveArmazenada,
  credentials: [],
  filtered: [],
  activeKey: null,   // string composta "nome::email"
  activeCred: null,
  editing: false,
  isNew: false,
  searchQuery: '',
  pendingDelete: null,
  freshKey: false,   // true quando a chave veio do gerador (não do cofre existente)
  sortKey: 'nome',   // 'nome' | 'atualizado' | 'dominio'
  sortDir: 'asc',    // 'asc' | 'desc'
  showDuplicatesOnly: false,
  showExpiringOnly: false,
  showWeakOnly: false,
  activeTagFilters: new Set(),
};

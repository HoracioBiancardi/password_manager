export const st = {
  masterKey: localStorage.getItem('pm_key') || sessionStorage.getItem('pm_key') || null,
  credentials: [],
  filtered: [],
  activeKey: null,   // string composta "nome::email"
  activeCred: null,
  editing: false,
  isNew: false,
  searchQuery: '',
  pendingDelete: null,
  freshKey: false,   // true quando a chave veio do gerador (não do vault existente)
  sortKey: 'nome',   // 'nome' | 'atualizado' | 'dominio'
  sortDir: 'asc',    // 'asc' | 'desc'
  showDuplicatesOnly: false,
};

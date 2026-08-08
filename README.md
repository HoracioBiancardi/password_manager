# PS Manager V2 (SwordPower)

Gerenciador de senhas e cofre cifrado Zero-Knowledge construído sobre a arquitetura padronizada **SwordPower Web Starter**.

## ✨ Destaques V2

- **UI Desenvolvedor Moderna**: Tema Corporativo (`corporate` - Padrão) e Verde Escuro Neutro (`green-neutral`), visual glassmorphism, badge SVG SwordPower e fundo animado Aurora.
- **Armazenamento Cifrado Zero-Knowledge**: Dados armazenados em disco cifrados com Fernet (AES-128). Chaves mantidas estritamente na memória RAM com Auto-Lock por inatividade.
- **Banner de Alertas Corporativo**: Alertas visuais integrados de senhas fracas, reutilizadas e credenciais prestes a expirar.
- **Ferramentas de Vault**:
  - Gerador de senhas fortes com parâmetros ajustáveis.
  - Filtro por tags, favoritas, duplicadas, fracas e expirando.
  - Importação/Exportação nos formatos JSON, CSV e Encrypted `.enc`.
  - Bookmarklet de preenchimento automático em páginas web.

## 🚀 Como Executar

```bash
cd /home/swordpower/Documentos/REPO/PESSOAL/ps_managerV2
python3 -m uvicorn ps_manager.main:app --reload --port 8000
```

Acesse em **`http://127.0.0.1:8000`**.

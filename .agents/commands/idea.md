---
name: idea
description: Gerencia o Cofre de Ideias. Suporta auto-roteamento por projeto, consulta específica (/idea [projeto] ou /ideias_[projeto]) e salvamento global/local.
---

# /idea — Sistema Roteado de Ideias (Local & Global)

## Sintaxe e Comportamentos:
1. **`/idea` ou `/ideias`** (Sem parâmetros):
   - Exibe o Cofre Global (`ideasVault.md`) + o contador de ideias locais de cada projeto ativo.
2. **`/idea [projeto]` ou `/ideias_[projeto]`** (Ex: `/idea rpg_tarot`, `/ideias_pci_site`):
   - Realiza o *fetch* direto no `.agents/ideas.md` daquele repositório e exibe suas ideias na hora.
3. **`/idea [texto da ideia]`**:
   - Se o texto mencionar um projeto ativo, o Atlas grava a ideia diretamente no `.agents/ideas.md` do projeto.
   - Se não mencionar nenhum projeto, grava no Cofre Global (`ideasVault.md`).

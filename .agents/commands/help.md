# 📖 Guia de Comandos e Capacidades do Sistema (Atlas / Antigravity)

Este guia reúne todos os comandos, skills, hooks, regras e subagentes disponíveis no ecossistema atual.

---

## 💻 1. Slash Commands Disponíveis (`commands/`)

| Comando | Descrição | Ação Associada |
| :--- | :--- | :--- |
| **`/help`** | Exibe este guia completo de comandos e capacidades do sistema. | Exibe a documentação geral do ecossistema. |
| **`/idea [texto]`** | Registra uma nova ideia ou **exibe o cofre** se usado sozinho. | Dispara a Skill `sk_idea_vault`. |
| **`/suggest-automation`** | Varre o histórico recente de interações e sugere automações proativas. | Dispara a Skill `sk_pattern_packager`. |
| **`/crystallize-rule`** | Força a gravação de uma orientação ditada pelo João como uma regra oficial. | Dispara a gravação em `rules/`. |
| **`/conselho [proposta]`** | Convoca a Sessão Plenária do Conselho dos Seis Chapéus de IA. | Dispara a sabatina modular em `.agents/council/`. |


---

## 🛠️ 2. Kit Atômico de Skills Globais & Scripts Universais (`skills/` & `scripts/`)

- **`sk_read_file.md`** *(Script: `scripts/read_file.py`)*: Leitura segura de arquivos (.txt, .md, .json, .csv, .pdf, .yaml).
- **`sk_write_file.md`** *(Script: `scripts/write_file.py`)*: Criação, sobrescrita e apêndice de arquivos e diretórios.
- **`sk_move_file.md`** *(Script: `scripts/move_file.py`)*: Movimentação e renomeação segura de arquivos e pastas.
- **`sk_delete_file.md`** *(Script: `scripts/delete_file.py`)*: Exclusão e limpeza segura de arquivos temporários.
- **`sk_audit_directory.md`** *(Script: `scripts/audit_directory.py`)*: Inspeção e varredura de diretórios no SO.
- **`sk_update_memory.md`** *(Script: `scripts/update_memory.py`)*: Atualização atômica de seções nos arquivos de memória viva (.md).
- **`sk_idea_vault.md`** *(Script: `scripts/save_idea.py`)*: Captura, lapidação e exibição do Cofre de Ideias (`ideasVault.md`).
- **`sk_ocultar_elementos.md`** *(Script: `scripts/hide_path.py`)*: Oculta qualquer arquivo ou pasta no Windows via `attrib +h`.
- **`sk_pattern_packager.md`** *(Script: `scripts/package_pattern.py`)*: Empacota propostas de automação a partir de padrões de uso.
- **`sk_builder_dispatcher.md`** *(Script: `scripts/dispatch_builder.py`)*: Seleciona e aciona o subagente construtor correto em background.

---

## ⚙️ 3. Hooks de Evento em Segundo Plano (`hooks/` & `hooks.json`)

- **`GameSaveWatcher.py`**: Oculta automaticamente pastas de saves de jogos geradas na raiz de `Documents`.
- **`PatternDetectorHook.py`**: Escuta repetições de tarefas para acionar o auto-incremento.
- **`DirectiveCatcherHook.py`**: Escuta frases de instrução do João para propor a gravação de novas regras.

---

## 🤖 4. Quarteto de Subagentes Construtores em Background

- **`SKILL_CREATOR_AGENT`**: Constrói novas Skills (`sk_snake_case.md`).
- **`SCRIPT_CREATOR_AGENT`**: Constrói scripts Python reutilizáveis e atômicos (`snake_case.py` — DRY e SRP).
- **`COMMAND_CREATOR_AGENT`**: Constrói Slash Commands (`kebab-case.md`).
- **`HOOK_CREATOR_AGENT`**: Constrói Handlers de Evento (`PascalCase.py` + `hooks.json`).

---

## 📜 5. Regras de Governança Globais (`rules/`)

- **`00_privacy_rule.md`**: Sigilo absoluto da pasta `00_Documentos_Pessoais` (gravação por demanda, sem leitura).
- **`hidden.folder.rule.md`**: Classificação em 3 categorias de diretórios (Trabalho, Artefato Externo, Triagem).
- **`atlas.auto.increment.rule.md`**: Regra mestre do motor de auto-aprimoramento.
- **`atlas.transparency.rule.md`**: Transparência ativa proporcional do Secretário Atlas.


## 📜 5. Regras de Governança Globais (
ules/)
- **tlas.standby.panel.rule.md**: Regra mestre que exige a apresentação do Painel dos Supervisores sempre no estado padrão de aguardo.


## 📜 5. Regras de Governança Globais (
ules/)
- **supervisor.git.commit.rule.md**: Regra obrigatória exigindo que todos os commits do Git criados pelos Supervisores sejam escritos em Português (PT-BR).


## 💻 3. Comandos de Atalho (`commands/`)
- - **`/home`**: Reseta a sessão para o estado neutro e exibe o Hub Central (Supervisores, Downloads, Ideias, Saúde do Sistema e Métricas do Ecossistema).

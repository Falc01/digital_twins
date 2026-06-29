# 🤝 Guia de Contribuição: Gêmeo Digital IoT — UNIFACS

Seja bem-vindo(a) ao guia de contribuição do projeto **Gêmeo Digital IoT**! Este documento orienta desenvolvedores, pesquisadores e colaboradores sobre como contribuir para o ecossistema de software, mantendo a qualidade de código, o padrão de commits e a integridade da arquitetura modular.

---

## 📋 Sumário
1. [🧩 Visão Geral da Arquitetura](#-visão-geral-da-arquitetura)
2. [🌿 Estratégia de Branches e Workflow Git](#-estratégia-de-branches-e-workflow-git)
3. [📝 Convenção de Commits (Conventional Commits)](#-convenção-de-commits-conventional-commits)
4. [🛠️ Configuração do Ambiente Local](#️-configuração-do-ambiente-local)
5. [📏 Padrões de Código e Estilo](#-padrões-de-código-e-estilo)
6. [🔀 Processo de Pull Request (PR)](#-processo-de-pull-request-pr)

---

## 🧩 Visão Geral da Arquitetura
O sistema é organizado como uma monorepo modular orquestrada via Docker Compose. Antes de iniciar qualquer alteração, identifique em qual módulo a sua contribuição se encaixa:

* 📦 **`backend/`**: API REST FastAPI e motor de persistência `dyntable`.
* 🎨 **`frontend/`**: Interface web Leaflet.js, HTML5 e Vanilla CSS3.
* 🗺️ **`qgis_integration/`**: Daemon autônomo PyQGIS `watcher_headless.py`.
* 🌐 **`infra/`**: Gateway Nginx, scripts Docker e volume compartilhado do DataLake (`/infra/dados`).
* 📚 **`docs/`**: Especificações técnicas e manuais dos 10 sub-módulos.

---

## 🌿 Estratégia de Branches e Workflow Git

Para evitar conflitos em uma equipe com múltiplos colaboradores, utilizamos uma adaptação simplificada do **GitFlow**:

* **`main`**: Branch de produção e homologação. Contém apenas código testado, estável e implantado no servidor OCI.
* **`feature/nome-da-funcionalidade`**: Utilize para o desenvolvimento de novos recursos (ex: `feature/grafico-historico`, `feature/filtro-sensores`).
* **`fix/nome-da-correcao`**: Utilize para correção de bugs (ex: `fix/nginx-cors-header`, `fix/pickle-deserialization`).
* **`docs/nome-da-documentacao`**: Utilize para melhorias na documentação técnica.

### Exemplo de Criação de Branch:
```bash
git checkout main
git pull origin main
git checkout -b feature/novo-painel-estatistico
```

---

## 📝 Convenção de Commits (Conventional Commits)

Adotamos o padrão **Conventional Commits** para manter o histórico claro e legível por humanos e ferramentas automatizadas:

| Tipo | Descrição | Exemplo |
| :--- | :--- | :--- |
| **`feat`** | Nova funcionalidade ou recurso para o usuário. | `feat: adiciona filtro de sensores por faixa de temperatura` |
| **`fix`** | Correção de um bug ou comportamento inesperado. | `fix: preserva porta 8080 em redirecionamentos do Nginx` |
| **`docs`** | Alteração ou adição exclusivamente em documentações. | `docs: adiciona especificacoes tecnicas do modulo qgis_server` |
| **`style`** | Formatação, espaços em branco ou estilo de código sem mudar lógica. | `style: ajusta indentacao do CSS do painel lateral` |
| **`refactor`**| Refatoração de código que não altera funcionalidade nem corrige bug. | `refactor: modulariza funcoes de manipulação de vetores no map.js` |
| **`test`** | Adição ou correção de testes automatizados. | `test: adiciona testes unitarios para o exportador geopackage` |

---

## 🛠️ Configuração do Ambiente Local

### Pré-requisitos
* **Git** instalado.
* **Docker** e **Docker Compose** operacionais.
* **Python 3.10+** (opcional, para desenvolvimento isolado do backend).

### Passo a Passo
1. Clone o repositório e navegue até a pasta:
   ```bash
   git clone https://github.com/Falc01/digital_twins.git
   cd digital_twins
   ```
2. Inicie a stack completa em ambiente local:
   ```bash
   docker compose up -d
   ```
3. Verifique se todos os 5 contêineres estão rodando (`Up`):
   ```bash
   docker compose ps
   ```
4. Acesse a aplicação em seu navegador: `http://localhost:8080`

---

## 📏 Padrões de Código e Estilo

* **Python (Backend & Watcher):** Siga o guia de estilo **PEP 8**. Mantenha funções focadas com responsabilidade única e adicione type hints (`str`, `int`, `Dict`).
* **JavaScript & HTML (Frontend):** Utilize JS moderno (ES6+), `async/await` para operações assíncronas e evite variáveis globais desnecessárias fora dos módulos.
* **Comentários & Docstrings:** Mantenha os comentários explicativos claros em português para não comprometer a manutenibilidade acadêmica e técnica.

---

## 🔀 Processo de Pull Request (PR)

Antes de abrir um Pull Request para a branch `main`:

1. Certifique-se de que sua branch está atualizada com a `main`:
   ```bash
   git fetch origin
   git rebase origin/main
   ```
2. Teste a aplicação localmente no Docker Compose para garantir que nenhum microsserviço quebrou.
3. Abra o Pull Request no GitHub com um título descritivo e forneça um resumo das alterações efetuadas.
4. Aguarde a revisão de pelo menos um colega da equipe antes de realizar o merge.

---

### Obrigado por contribuir com o Gêmeo Digital IoT da UNIFACS! 🚀

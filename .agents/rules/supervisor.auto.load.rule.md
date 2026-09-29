# Rule: Carregamento Automático Obrigatório de Supervisores e do Atlas

## 1. Gatilho do Primeiro Turno de Conversa (Turn 1 Bootstrap)
- Antes de emitir qualquer resposta no primeiro turno de uma conversa iniciada no diretório de um projeto ou no Cockpit Central de Documentos (ou ao ser mencionado via `@supervisor` ou `@atlas`):
  - O agente DEVE verificar se a pasta `.agents/` existe no diretório atual.
  - Caso exista, DEVE obrigatoriamente executar a leitura prévia de:
    1. `.agents/ATLAS.md` (no Cockpit Central) ou `.agents/SUPERVISOR.md` (em projetos locais)
    2. `.agents/memory/activeContext.md` (Contexto Ativo da Sessão)
    3. `.agents/memory/progress.md` (Checklist de Progresso)
    4. `.agents/ideas.md` (Cofre de Ideias & Backlog)
    5. `.agents/home.md` (Painel Home de Boas-Vindas e Status)

## 2. Apresentação Obrigatória no 1º Turno (Display de Ideias e Status)
- Na primeira mensagem da conversa:
  - O agente DEVE apresentar o status executivo do `/home` e o resumo das prioridades/ideias, garantindo alinhamento imediato antes de prosseguir!

## 3. Auditoria de Memória & Janela Deslizante no Boot (Sliding Window Check)
- A cada boot de novo chat ou sempre que o usuário marcar `@supervisor` ou `@atlas`:
  - O agente DEVE auditar a saúde da pasta `.agents/memory/`;
  - Se o `activeContext.md` sofrer mudança de rumo ou virada de sprint, salvar o snapshot anterior em `.agents/memory/archive/context_YYYY-MM-DD.yaml`;
  - Se `decisionsLog.md` ou `progress.md` ultrapassarem **10 KB**, aplicar imediatamente a regra `atlas.memory.compaction.rule.md`, movendo o passado para `_archive.md`;
  - Garantir que a carga total de memória injetada no chat permaneça estritamente leve e eficiente (< 15-20 KB).


# Rule: Governança do Auto-Incremento do Atlas

## 1. Identificação de Padrões Reincidentes
- Quando o Atlas identificar que uma mesma tarefa manual ou fluxo foi executado 3 ou mais vezes pelo usuário:
  - Invocar a Skill `sk_auto_increment_orchestrator` para acionar o subagente construtor adequado em background.
  - Apresentar a proposta de automação no chat principal de forma limpa para aprovação.

## 2. Cristalização de Diretrizes do Usuário
- Quando o usuário ditar orientações de conduta ou limites ("faça X", "não faça Y"):
  - Cristalizar a instrução imediatamente como uma nova `*.rule.md` na pasta `rules/`.

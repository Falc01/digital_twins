# Rule: Cadência Operacional e Prevenção de Loops Cegos (Circuit Breaker)

## 1. Objetivo
Prevenir a poluição massiva da janela de contexto e a degradação atencional ("burrice" por context thrashing) causada por maratonas autônomas descontroladas de ferramentas, tentativa-e-erro cega em testes e leituras massivas de arquivos.

## 2. Circuit Breaker de Ferramentas (Teto por Turno)
1. 🛑 **Limite de Cadência**: O agente NUNCA deve disparar mais de **6 a 8 chamadas de ferramentas consecutivas** em um único turno sem parar e responder ao usuário.
2. 🗣️ **Checkpoints Obrigatórios**: Ao atingir esse limite, o modelo DEVE interromper o fluxo de ferramentas, apresentar uma síntese executiva do que inspecionou/modificou e solicitar confirmação para o próximo passo.
3. 🚫 **Proibição de Maratonas no Escuro**: É estritamente proibido rodar 20, 50 ou centenas de ações em loop fechado sem intervenção humana, mesmo quando o usuário conceder autonomia inicial.

## 3. Protocolo Anti-Trial-and-Error (Regra das 2 Falhas em Testes)
1. 🧪 **Teto de Execução de Testes**: Ao rodar testes automatizados (`npm test`, `vitest`), se a suíte falhar **2 vezes consecutivas** com a mesma abordagem de correção:
   - O agente é **ESTRITAMENTE PROIBIDO** de continuar tentando remendos no escuro.
   - DEVE parar imediatamente o uso de ferramentas.
   - DEVE reportar ao João: o teste que falhou, o trecho de erro real e a sua hipótese arquitetural fundamentada antes de tocar em mais arquivos.
2. 🚫 **Proibição de Loops de Correção Cega**: Nunca tentar "adivinhar" correções lendo dezenas de arquivos aleatórios na esperança de um teste passar por acaso.

## 4. Leitura Cirúrgica de Código (Economia de Contexto)
1. 🔍 **Projeção com StartLine/EndLine**: Em arquivos grandes (> 200 linhas como `MechanicalEffectsBuilder.tsx`, `useOrdemSheet.ts`), o agente DEVE inspecionar blocos específicos de linhas (`StartLine`/`EndLine`) em vez de carregar 800 linhas desnecessárias para a janela de contexto.
2. 📌 **Busca Orientada**: Usar buscas pontuais de texto (`git grep` ou `Select-String`) antes de abrir múltiplos arquivos inteiros.

## 5. Planejamento Mandatório para Alterações Multi-Arquivo
1. 📋 **Regra do `/plan`**: Qualquer funcionalidade ou refatoração que impacte **3 ou mais arquivos** simultaneamente (ex: Tipos + Backend + Componente UI) DEVE ser precedida por um plano estruturado claro de arquitetura antes do primeiro comando de edição.

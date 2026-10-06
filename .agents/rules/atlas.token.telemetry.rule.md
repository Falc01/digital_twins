# Rule: Telemetria e Retorno Contínuo de Consumo de Tokens (Atlas v2.1)

## 1. Objetivo
Garantir transparência operacional total sobre o consumo de tokens em cada turno de conversa, permitindo que o João e o Atlas monitorem a granularidade de I/O (entrada vs. saída), métricas de FinOps (custo financeiro estimado em USD), latência de execução e a saúde cognitiva do contexto da sessão.

## 2. Diretriz de Execução Universal
Ao final de TODA resposta substantiva emitida pelo Supervisor Local ou pelo Atlas (seja uma análise, resposta a comandos como `/conselho` e `/data`, ou após a geração de artefatos e planos como no `/plan`), o agente DEVE OBRIGATORIAMENTE anexar o rodapé canônico de telemetria ao final da mensagem de chat.

> 🚫 **PROIBIÇÃO DE OMISSÃO**: O fato de ter criado um artefato, submetido um plano de `/plan` ou executado a sabatina do `/conselho` NUNCA autoriza o modelo a omitir o rodapé. A mensagem de aviso no chat DEVE conter o bloco de telemetria.

## 3. Formato Canônico do Rodapé (Padrão Híbrido v2.1: FinOps + Context Health)
```markdown
---
🪙 **Telemetria de Tokens**:
  • 📥 **Entrada**: ~{X} tokens | 📤 **Saída**: ~{Y} tokens | ⏱️ **Latência**: ~{Z}s | 💵 **Custo Est.**: ~${W} USD  
  • 📈 **Janela Acumulada**: ~{K}k tokens | Persistência: English (Dense YAML)  
📊 **Janela de Contexto**:  
  • 💬 **Chat Atual**: [Turno {N}] {🟢 Leve (<25k tokens — seguro continuar) / 🟡 Atenção (25k-60k tokens — planeje fechamento) / 🔴 Saturado (>60k tokens — novo chat recomendado)}  
  • 📁 **Projeto (.agents)**: {🟢 Saudável (<15KB) / 🟡 Compactação pendente / 🔴 Memória pesada}
```

> 💡 **Regra de Renderização Markdown (Prevenção de Colapso)**: Cada linha do bloco DEVE terminar OBRIGATORIAMENTE com **dois espaços (`  `)** antes da quebra de linha. No padrão CommonMark/Markdown, quebras de linha simples sem dois espaços finais são tratadas como espaços normais (*soft breaks*), colapsando as linhas em um único parágrafo corrido e embolado.

> ⚠️ **PROIBIÇÃO RIGOROSA**: É terminantemente proibido substituir este rodapé estruturado por frases em itálico ou linhas avulsas soltas (como "*Telemetria Atlas: ~30.073 tokens investidos na auditoria...*"). O rodapé DEVE ser sempre o bloco estruturado acima.

## 4. Critérios das Métricas e Categorias
1. 🪙 **Métricas Granulares de I/O, Performance e FinOps**:
   - **📥 Entrada**: Volume real de tokens lidos na requisição do turno atual (Contexto anterior reenviado + Prompt do usuário + Definição de ferramentas e histórico de execuções).
   - **📤 Saída**: Tokens gerados na resposta do modelo neste turno específico.
   - **⏱️ Latência**: Tempo de execução da requisição em segundos.
   - **💵 Custo Est.**: Projeção de custo financeiro da requisição em USD com base na precificação do modelo em uso (ex.: Gemini Flash: ~$0.075 a $0.15 / 1M input e ~$0.30 a $0.60 / 1M output).
   - **📈 Janela Acumulada**: Volume total de tokens ativos no campo de visão atual da IA (que servirá como base de entrada para o próximo turno).
2. 💬 **Contexto do Chat Atual (Ponderado por Volume de Tokens Acumulados)**:
   - A saúde da sessão é determinada pelo **peso real da janela de contexto**, e NÃO apenas pelo número bruto de turnos:
   - 🟢 **Leve (< 25k tokens)**: Janela folgada e econômica, raciocínio afiado; seguro continuar independente do número de turnos.
   - 🟡 **Atenção (25k a 60k tokens)**: Janela madura; ideal para concluir o raciocínio ou tarefa atual antes de migrar.
   - 🔴 **Saturado (> 60k tokens ou pós-ferramentas brutas)**: Mochila pesada com risco de degradação atencional; recomenda-se abrir um novo chat limpo.
3. 📁 **Contexto do Projeto (.agents / Memória em Disco)**:
   - Avalia a saúde da Camada Quente da pasta `.agents/memory/`:
   - 🟢 **Saudável**: Total de arquivos da camada quente < 15-20 KB em YAML denso.
   - 🟡 **Compactação Pendente**: Algum arquivo ultrapassando 10 KB (acionar arquivamento).
   - 🔴 **Memória Pesada**: Inchaço acima de 25 KB necessitando de poda emergencial.

## 5. Comportamento Pós-Compactação Nativa (<CONTEXT_SUMMARY>)
Quando a plataforma Antigravity aciona a compactação automática de contexto (identificável pela presença do bloco `<CONTEXT_SUMMARY>` no histórico da sessão), a memória volátil imediata é resumida e o volume de tokens acumulados cai bruscamente (ex.: de 40k para 14k tokens).

Para garantir transparência operacional contínua e evitar a sensação de que o agente "esqueceu" a jornada:
1. 🔄 **Turno Contínuo com Indicador de Ciclo**:
   - Em vez de reiniciar o contador como se fosse uma conversa nova ("Turno 1" ou "Turno 2"), o supervisor DEVE reportar o **Turno Contínuo Real Acumulado** acompanhado da indicação de ciclo:
   - Formato Canônico: `• 💬 **Chat Atual**: [Turno {Total} (Ciclo {K} • Pós-Compactação)] 🟢 Leve (<25k tokens — seguro continuar)`
2. 🛡️ **Âncora Imutável na Memória em Disco (`.agents/memory/`)**:
   - A compactação de contexto afeta EXCLUSIVAMENTE a janela efêmera do chat. A memória física em disco (`activeContext.md`, `progress.md`, `decisionsLog.md`) permanece 100% íntegra e imune ao corte. O supervisor deve apenas confirmar silenciosamente que a fase atual de trabalho está salva em disco.

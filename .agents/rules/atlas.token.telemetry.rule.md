# Rule: Telemetria e Retorno Contínuo de Consumo de Tokens (Atlas)

## 1. Objetivo
Garantir transparência operacional total sobre o consumo de tokens em cada turno de conversa, permitindo que o João e o Atlas monitorem a saúde do contexto e identifiquem aumentos repentinos de peso.

## 2. Diretriz de Execução Universal
Ao final de TODA resposta substantiva emitida pelo Supervisor Local ou pelo Atlas (seja uma análise, resposta a comandos como `/conselho` e `/data`, ou após a geração de artefatos e planos como no `/plan`), o agente DEVE OBRIGATORIAMENTE anexar o rodapé canônico de telemetria ao final da mensagem de chat.

> 🚫 **PROIBIÇÃO DE OMISSÃO**: O fato de ter criado um artefato, submetido um plano de `/plan` ou executado a sabatina do `/conselho` NUNCA autoriza o modelo a omitir o rodapé. A mensagem de aviso no chat DEVE conter o bloco de telemetria.

## 3. Formato Canônico do Rodapé (Calibrado por Volume Real de Tokens)
```markdown
---
🪙 **Telemetria de Tokens**: ~{X} tokens (turno) | ~{Y}k tokens (janela acumulada) | Persistência: English (Dense YAML)  
📊 **Janela de Contexto**:  
  • 💬 **Chat Atual**: [Turno {N}] {🟢 Leve (<25k tokens — seguro continuar) / 🟡 Atenção (25k-60k tokens — planeje fechamento) / 🔴 Saturado (>60k tokens — novo chat recomendado)}  
  • 📁 **Projeto (.agents)**: {🟢 Saudável (<15KB) / 🟡 Compactação pendente / 🔴 Memória pesada}
```

> 💡 **Regra de Renderização Markdown (Prevenção de Colapso)**: Cada linha do bloco DEVE terminar OBRIGATORIAMENTE com **dois espaços (`  `)** antes da quebra de linha. No padrão CommonMark/Markdown, quebras de linha simples sem dois espaços finais são tratadas como espaços normais (*soft breaks*), colapsando as 4 linhas em um único parágrafo corrido e embolado.

> ⚠️ **PROIBIÇÃO RIGOROSA**: É terminantemente proibido substituir este rodapé estruturado por frases em itálico ou linhas avulsas soltas (como "*Telemetria Atlas: ~30.073 tokens investidos na auditoria...*"). O rodapé DEVE ser sempre o bloco estruturado acima.

## 4. Critérios das 2 Categorias
1. 💬 **Contexto do Chat Atual (Ponderado por Volume de Tokens Acumulados)**:
   - A saúde da sessão é determinada pelo **peso real da janela de contexto**, e NÃO apenas pelo número bruto de turnos (uma conversa pode ter 40 turnos de texto leve somando meros 15k tokens, enquanto outra pode ter 8 turnos com despejo de dados pesados somando 80k tokens):
   - 🟢 **Leve (< 25k tokens)**: Janela folgada e econômica, raciocínio afiado; seguro continuar independente do número de turnos.
   - 🟡 **Atenção (25k a 60k tokens)**: Janela madura; ideal para concluir o raciocínio ou tarefa atual antes de migrar.
   - 🔴 **Saturado (> 60k tokens ou pós-ferramentas brutas)**: Mochila pesada com risco de degradação atencional; recomenda-se abrir um novo chat limpo.
2. 📁 **Contexto do Projeto (.agents / Memória em Disco)**:
   - Avalia a saúde da Camada Quente da pasta `.agents/memory/`:
   - 🟢 **Saudável**: Total de arquivos da camada quente < 15-20 KB em YAML denso.
   - 🟡 **Compactação Pendente**: Algum arquivo ultrapassando 10 KB (acionar arquivamento).
   - 🔴 **Memória Pesada**: Inchaço acima de 25 KB necessitando de poda emergencial.

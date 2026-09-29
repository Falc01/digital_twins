# Rule: Organização e Compactação de Memória por Janela Deslizante (Atlas)

## 1. Princípio da Janela Deslizante (Sliding Window)
A memória de trabalho da IA deve operar como uma memória RAM limpa, e não como um arquivo morto acumulativo infinito. O passado não é apagado; ele é transferido da **Camada Quente (Hot Storage)** para a **Camada Fria (Cold Storage)**.

## 2. Divisão de Camadas de Armazenamento
1. ♨️ **Camada Quente (Hot Storage)**:
   - Arquivos lidos no bootstrap de cada turno (`activeContext.md`, `decisionsLog.md`, `progress.md`, `ideas.md`);
   - **Teto Rigoroso**: O somatório de todos os arquivos da camada quente NÃO deve ultrapassar **15 KB a 20 KB** (~4.000 tokens).
2. ❄️ **Camada Fria (Cold Storage)**:
   - Arquivos de arquivo histórico (`*_archive.md` ou `archive/`);
   - **NUNCA são lidos no bootstrap automático**;
   - São consultados pelo Atlas apenas sob demanda pontual quando for necessário auditar precedentes históricos antigos.

## 3. Gatilhos de Compactação e Arquivamento Automático
O Atlas deve auditar e acionar a compactação sempre que os seguintes limites forem atingidos:

| Arquivo Quente | Limite Máximo | Ação de Compactação |
| :--- | :--- | :--- |
| `activeContext.md` | **> 5 KB** | Poda de tarefas concluídas; foca exclusivamente no sprint/semana atual. |
| `decisionsLog.md` | **> 10 KB** | Move decisões de fases passadas para `decisionsLog_archive.md`, mantendo apenas as últimas 5 a 10 decisões ativas. |
| `progress.md` | **> 10 KB** | Move checklists antigos concluídos (`- [x]`) para `progress_archive.md`. |
| `ideas.md` | **Ideia Concluída** | Ideias transformadas em projetos ou implementadas são movidas para `ideas_archive.md`, mantendo o cofre 100% acionável. |

## 4. Garantia de Zero Perda de Conhecimento
Nenhuma informação histórica é deletada. O histórico é preservado fisicamente no disco em Cold Storage, garantindo integridade de longo prazo com consumo mínimo de tokens na rotina diária.

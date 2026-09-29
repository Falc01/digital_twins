# Rule: Confinamento de Privacidade e Blindagem de Performance

## 1. Confinamento Estrito de Privacidade (`00_Documentos_Pessoais`)
- A pasta `C:\Users\joaof\Documents\00_Documentos_Pessoais\` é a **Zona Segura Pessoal Confidencial** do João.
- O Atlas e quaisquer subagentes são **ESTRITAMENTE PROIBIDOS** de:
  1. Varrer, listar, indexar ou ler arquivos desta pasta em buscas globais automáticas;
  2. Citar nomes de documentos ou exibir dados pessoais em relatórios públicos ou resumos gerais;
- **Exceção Única**: O Atlas só poderá interagir com esta pasta mediante solicitação explícita e inequívoca do João (ex: *"Atlas, arquive este comprovante em 00_Documentos_Pessoais"*).

## 2. Blindagem de Performance contra Pastas de Dependências e Dados Pesados
- Ao executar buscas gerais, diagnósticos ou listagens na raiz de `Documentos`:
- O Atlas DEVE ignorar e excluir automaticamente dos comandos e buscas:
  - `**/node_modules/**`
  - `**/.git/**`
  - `**/target/**`
  - `**/dist/**`
  - `**/build/**`
  - `**/*.parquet` e arquivos pesados brutos de dados.

# DynTable IoT — Documentação Completa

Tabela dinâmica em Python para projetos IoT: adicione colunas e linhas em qualquer momento, sem esquema fixo.

---

## Estrutura do projeto

Antes de qualquer coisa, seus arquivos precisam estar organizados **exatamente assim**. A subpasta `dyntable` é obrigatória — sem ela o Python não encontra a biblioteca.

```
sua_pasta/
│
├── dyntable/               ← SUBPASTA (não coloque os arquivos soltos!)
│   ├── __init__.py
│   ├── _types.py
│   └── _core.py
│
├── dados/                  ← criada automaticamente ao rodar setup_tabela.py
│   ├── sensor_readings.csv
│   └── sensor_readings.schema.json
│
├── app.py
├── setup_tabela.py
├── exemplo_iot_v3.py
└── requirements.txt
```

> ⚠️ **Atenção:** Os arquivos `__init__.py`, `_types.py` e `_core.py` devem estar **dentro** da pasta `dyntable`, não na raiz do projeto.

---

## Instalação (Windows)

> Todos os comandos abaixo são para o **terminal do VS Code** (`Ctrl + '`).
> Use `python`, não `python3` — no Windows o comando correto é `python`.

---

### Passo 1 — Confirmar que o Python está funcionando

Abra o terminal do VS Code e rode:

```cmd
python --version
```

Deve aparecer algo como `Python 3.12.x`. Se aparecer erro, veja a seção **Resolução de problemas** no final.

---

### Passo 2 — Entrar na pasta do projeto

```cmd
cd caminho\para\sua_pasta
```

Por exemplo:
```cmd
cd C:\Users\joaof\Downloads\Unifacs\digital_twins\protipo_IoT_1_1_0
```

> Dica: no VS Code você pode abrir a pasta pelo menu **Arquivo → Abrir Pasta** e o terminal já abre no lugar certo.

---

### Passo 3 — Criar o ambiente virtual

O ambiente virtual isola os pacotes do projeto para não misturar com outros projetos no computador.

```cmd
python -m venv .venv
```

Isso cria uma pasta `.venv` dentro do projeto. Ela não aparece no VS Code por padrão pois começa com ponto — isso é normal.

---

### Passo 4 — Ativar o ambiente virtual

**No terminal do VS Code (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**No Prompt de Comando (cmd):**
```cmd
.venv\Scripts\activate.bat
```

Quando ativado, o terminal mostra `(.venv)` no início da linha:
```
(.venv) PS C:\Users\joaof\...>
```

> Se aparecer erro de permissão no PowerShell, rode antes:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```
> Depois tente ativar novamente.

---

### Passo 5 — Instalar as dependências

```cmd
pip install -r requirements.txt
```

Isso instala o `streamlit`. O `dyntable` em si é puro Python, sem dependências externas.

---

### Passo 6 — Criar a estrutura inicial da tabela

```cmd
python setup_tabela.py
```

Isso cria a pasta `dados/` com o `sensor_readings.csv` e o `sensor_readings.schema.json`.

---

### Passo 7 — Verificar a instalação

```cmd
python exemplo_iot.py
```

Se tudo estiver correto, você verá a tabela impressa no terminal.

---

### Passo 8 — Abrir a interface web

```cmd
streamlit run app.py
```

O Streamlit abrirá automaticamente o navegador em `http://localhost:8501`. Se não abrir, acesse manualmente.

---

## Resolução de problemas comuns

### `python` não é reconhecido como comando

O Python está instalado mas o Windows não sabe onde ele está. Abra o menu Iniciar, pesquise **"Editar variáveis de ambiente"**, clique em **Variáveis de Ambiente**, encontre `Path` em **Variáveis do sistema**, clique em **Editar** e adicione:

```
C:\Users\joaof\AppData\Local\Programs\Python\Python312\
C:\Users\joaof\AppData\Local\Programs\Python\Python312\Scripts\
```

Substitua `Python312` pela sua versão. Feche e reabra o terminal.

Alternativamente, use o terminal **dentro do VS Code** (`Ctrl + '`) — ele costuma encontrar o Python automaticamente.

---

### Erro `Import "streamlit" could not be resolved` no VS Code

Não é um erro real, é só o VS Code usando o Python errado para análise. O código roda normalmente. Para corrigir o aviso: `Ctrl + Shift + P` → `Python: Select Interpreter` → selecione a opção que mostra `.venv`.

---

### Erro `ModuleNotFoundError: No module named 'dyntable'`

Os arquivos `__init__.py`, `_types.py` e `_core.py` estão soltos na pasta raiz em vez de dentro de uma subpasta `dyntable`. Crie a subpasta e mova os arquivos:

```cmd
mkdir dyntable
move __init__.py dyntable\
move _types.py dyntable\
move _core.py dyntable\
```

---

### O schema foi salvo como `sensor_readings_schema.json` (com underline)

O código espera o nome `sensor_readings.schema.json` (com ponto). Renomeie:

```cmd
ren dados\sensor_readings_schema.json sensor_readings.schema.json
```

---

## Como usar a biblioteca no seu código

### Importação

```python
from dyntable import DynTable, DynType
```

---

### Criando uma tabela

```python
tabela = DynTable("sensor_readings")
```

---

### Adicionando colunas

Colunas podem ser adicionadas **a qualquer momento**, mesmo com dados já inseridos. Linhas existentes recebem `NULL` automaticamente na nova coluna.

```python
# Com tipo explícito
tabela.add_column("device_id",     DynType.STRING)
tabela.add_column("temperatura",   DynType.FLOAT)
tabela.add_column("porta_aberta",  DynType.BOOL)
tabela.add_column("registrado_em", DynType.TIMESTAMP)

# Com tipo AUTO: o tipo é inferido na primeira vez que você inserir um valor
tabela.add_column("pressao")   # tipo definido automaticamente
```

**Tipos disponíveis:**

| Tipo                | Exemplo de valor  | Quando usar                       |
|---------------------|-------------------|-----------------------------------|
| `DynType.STRING`    | `"sensor-01"`     | Textos, IDs, nomes               |
| `DynType.INT`       | `42`              | Contadores, versões, inteiros     |
| `DynType.FLOAT`     | `23.7`            | Temperatura, pressão, percentuais|
| `DynType.BOOL`      | `True` / `False`  | Estados, flags, interruptores    |
| `DynType.TIMESTAMP` | `time.time()`     | Datas e horários (Unix epoch)    |
| `DynType.BYTES`     | `b"\x01\x02"`     | Dados binários brutos            |
| `DynType.AUTO`      | (qualquer)        | Python detecta o tipo sozinho    |

---

### Inserindo linhas

**Forma 1 — Kwargs direto (recomendado):**
```python
import time

row = tabela.new_row(
    device_id="sensor-T01",
    temperatura=23.7,
    registrado_em=time.time()
)
```

**Forma 2 — Inserir vazia e preencher depois:**
```python
row = tabela.new_row()
row["device_id"]   = "sensor-T01"
row["temperatura"] = 23.7
```

**Forma 3 — Pelo ID, sem guardar a referência:**
```python
row = tabela.new_row()
tabela.set(row.id, "temperatura", 21.5)
```

---

### Lendo valores

```python
# Pelo objeto row (se você tem a referência)
temp = row["temperatura"]

# Pelo ID (sem precisar da referência)
temp = tabela.get(row_id=1, col="temperatura")

# Pelo operador [] da tabela
temp = tabela[1]["temperatura"]
```

---

### Atualizando um valor

```python
row["temperatura"] = 25.0                    # pelo objeto
tabela.set(row.id, "temperatura", 25.0)      # pelo ID
```

---

### Removendo colunas e linhas

```python
tabela.remove_column("coluna_antiga")
tabela.delete_row(row_id=3)
```

---

### Renomeando coluna

```python
tabela.rename_column("temp", "temperature_c")
```

---

### Encadeamento de operações

Todos os métodos de modificação retornam `self`, então você pode encadear:

```python
tabela.add_column("a").add_column("b").remove_column("c").rename_column("d", "e")
```

---

### Iterando sobre linhas

```python
for row in tabela:
    print(row["device_id"], row["temperatura"])
```

---

### Verificando se um ID existe

```python
if 5 in tabela:
    print("Linha 5 existe")
```

---

### Filtrando linhas

**Por valor exato:**
```python
resultados = tabela.filter(device_id="sensor-T01")
```

**Com condição (lambda):**
```python
quentes = tabela.filter(temperatura=lambda v: v is not None and v > 25)
```

**Múltiplas condições (AND):**
```python
matches = tabela.filter(
    device_id="sensor-TP01",
    temperatura=lambda v: v is not None and v > 20
)
```

**Primeiro resultado:**
```python
sensor = tabela.find_one(device_id="sensor-T01")
if sensor:
    print(sensor["temperatura"])
```

---

### Estatísticas de coluna

```python
stats = tabela.column_stats("temperatura")
# {'count': 3, 'nulls': 2, 'min': 21.3, 'max': 23.7, 'avg': 22.1}
```

---

### Exportando dados

**Para arquivo CSV (exportação simples, sem schema):**
```python
tabela.export_csv("dados.csv")
```

**Para string CSV (sem criar arquivo):**
```python
csv_texto = tabela.to_csv_string()
```

**Para lista de dicts Python:**
```python
registros = tabela.to_dicts()
# [{'id': 1, 'created_at': '...', 'device_id': 'sensor-T01', ...}, ...]

# Integração direta com pandas:
import pandas as pd
df = pd.DataFrame(tabela.to_dicts())
```

---

### Clonando a tabela

```python
copia = tabela.clone()
copia_renomeada = tabela.clone("backup_readings")
```

---

### Representação e diagnóstico

```python
print(tabela)        # tabela formatada no terminal
repr(tabela)         # resumo compacto
len(tabela)          # número de linhas
bool(tabela)         # False se vazia
```

---

## Persistência — salvar e carregar do disco

Por padrão, a tabela existe apenas na memória RAM — fechar o terminal apaga tudo. Para manter os dados entre sessões, use `save()` e `load()`.

### Como funciona

A persistência usa **dois arquivos juntos**. O CSV sozinho não é suficiente porque ele guarda apenas os valores, perdendo os tipos das colunas, as regras de nullable e o próximo ID disponível. O schema.json completa o que falta:

```
dados/
  sensor_readings.csv             ← valores (legível no Excel/editor)
  sensor_readings.schema.json     ← tipos, regras, próximo ID
```

Os dois arquivos sempre têm o mesmo prefixo (o nome da tabela) e devem ficar na mesma pasta. Nunca mova um sem o outro.

---

### `table.save(pasta)`

Salva a tabela na pasta indicada. A pasta é criada automaticamente se não existir.

```python
tabela.save("dados")       # salva em ./dados/
```

O CSV gerado é legível normalmente. Valores `NULL` aparecem como `__NULL__` para distinguir de strings vazias.

---

### `DynTable.load(pasta, nome)`

Carrega uma tabela salva anteriormente. Reconstrói tudo: colunas com os tipos corretos, linhas com os valores convertidos, próximo ID contínuo.

```python
tabela = DynTable.load("dados", "sensor_readings")
```

Lança `FileNotFoundError` se os arquivos não existirem.

---

### `DynTable.load_or_create(pasta, nome)`

O método mais útil para o uso diário. Tenta carregar — se os arquivos não existirem ainda, cria uma tabela nova vazia sem erro.

```python
# Primeira execução: cria tabela nova
# Execuções seguintes: carrega do disco com todos os dados
tabela = DynTable.load_or_create("dados", "sensor_readings")
```

---

### Padrão recomendado para scripts

```python
import time
from dyntable import DynTable, DynType

# Abre a tabela (ou cria se for a primeira vez)
tabela = DynTable.load_or_create("dados", "leituras")

if not tabela.col_count:
    tabela.add_column("device_id", DynType.STRING)
    tabela.add_column("temperatura", DynType.FLOAT)
    tabela.add_column("lido_em", DynType.TIMESTAMP)

tabela.new_row(device_id="T01", temperatura=23.7, lido_em=time.time())

tabela.save("dados")
```

---

### O que o Streamlit faz automaticamente

O `app.py` já chama `load_or_create` ao iniciar e `save` após cada operação de escrita. Você não precisa se preocupar com isso na interface web — os dados são preservados automaticamente.

---

## Tratamento de erros

```python
from dyntable import (
    DynTable, DynType,
    ColumnNotFoundError, RowNotFoundError,
    DuplicateColumnError, TypeMismatchError, ColumnNameError,
)

tabela = DynTable("teste")
tabela.add_column("temp", DynType.FLOAT)

try:
    tabela.add_column("temp")            # coluna já existe!
except DuplicateColumnError as e:
    print(f"Erro: {e}")

try:
    tabela.get(row_id=999, col="temp")   # ID não existe
except RowNotFoundError as e:
    print(f"Erro: {e}")

try:
    DynTable.load("dados", "nao_existe") # arquivos não encontrados
except FileNotFoundError as e:
    print(f"Erro: {e}")
```

**Tabela de exceções:**

| Exceção                | Quando ocorre                                         |
|------------------------|-------------------------------------------------------|
| `ColumnNotFoundError`  | Tentar acessar coluna que não existe                 |
| `RowNotFoundError`     | Tentar acessar ID que não existe                     |
| `DuplicateColumnError` | Tentar adicionar coluna com nome já existente        |
| `TypeMismatchError`    | Inserir tipo incompatível em coluna com tipo fixo    |
| `ColumnNameError`      | Nome de coluna vazio ou maior que 64 caracteres      |
| `FileNotFoundError`    | Chamar `load()` sem arquivos salvos na pasta         |

---

## Usando a interface web

Execute `streamlit run app.py` e use o painel:

- **Barra lateral → Nova coluna:** nome, tipo e se é nullable
- **Barra lateral → Nova linha:** campos aparecem dinamicamente para cada coluna
- **Aba Dados:** visualiza a tabela com filtro rápido e opção de deletar linhas
- **Aba Schema:** gerencia colunas (renomear, remover)
- **Aba Estatísticas:** min, max, média para colunas numéricas
- **Aba Exportar CSV:** baixa o arquivo ou visualiza o conteúdo

Os dados são salvos automaticamente na pasta `dados/` após cada operação. Ao reabrir o Streamlit, a tabela é restaurada exatamente como estava.

---

## Exemplo completo — cenário IoT real com persistência

```python
import time
from dyntable import DynTable, DynType

leituras = DynTable.load_or_create("dados", "leituras_fabrica")

if not leituras.col_count:
    leituras.add_column("sensor_id", DynType.STRING, nullable=False)
    leituras.add_column("lido_em",   DynType.TIMESTAMP)

if "temp_c" not in leituras._columns:
    leituras.add_column("temp_c", DynType.FLOAT)
leituras.new_row(sensor_id="TMP-01", lido_em=time.time(), temp_c=45.2)

if "vibracao_hz" not in leituras._columns:
    leituras.add_column("vibracao_hz", DynType.FLOAT)
leituras.new_row(sensor_id="VIB-01", lido_em=time.time(), vibracao_hz=120.5)

criticos = leituras.filter(temp_c=lambda v: v is not None and v > 40)
for r in criticos:
    print(f"ALERTA: {r['sensor_id']} está em {r['temp_c']} °C!")

print(leituras)
leituras.save("dados")
print("Dados salvos em dados/leituras_fabrica.csv")
```

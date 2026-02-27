# DynTable IoT — Documentação Completa

Tabela dinâmica em Python para projetos IoT: adicione colunas e linhas em qualquer momento, sem esquema fixo.

---

## Estrutura do projeto

```
dyntable-iot/
│
├── dyntable/               ← pacote principal (sua "biblioteca")
│   ├── __init__.py         ← interface pública
│   ├── _types.py           ← tipos, exceções, constantes
│   └── _core.py            ← implementação da DynTable
│
├── app.py                  ← interface web (Streamlit)
├── exemplo_iot.py          ← script de exemplo
└── requirements.txt        ← dependências
```

---

## Instalação

### Passo 1 — Ter o Python instalado

Verifique no terminal:

```bash
python3 --version
```

Precisa ser **Python 3.10 ou superior**. Se não tiver, baixe em [python.org](https://www.python.org/downloads/).

---

### Passo 2 — Criar um ambiente virtual

Um ambiente virtual isola as dependências do projeto do resto do seu sistema. É uma boa prática sempre fazer isso.

```bash
# Entre na pasta do projeto
cd dyntable-iot

# Crie o ambiente virtual (cria uma pasta chamada .venv)
python3 -m venv .venv
```

---

### Passo 3 — Ativar o ambiente virtual

**No Linux/macOS:**
```bash
source .venv/bin/activate
```

**No Windows (Prompt de Comando):**
```cmd
.venv\Scripts\activate.bat
```

**No Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

Quando ativado, o terminal mostra `(.venv)` no início da linha. Para sair do ambiente: `deactivate`.

---

### Passo 4 — Instalar as dependências

```bash
pip install -r requirements.txt
```

Isso instala apenas o `streamlit` (necessário para a interface web). O `dyntable` em si é puro Python, sem dependências externas.

---

### Passo 5 — Verificar a instalação

```bash
python3 exemplo_iot.py
```

Se tudo estiver correto, você verá a tabela impressa no terminal.

---

### Passo 6 — Abrir a interface web

```bash
streamlit run app.py
```

O Streamlit abrirá automaticamente o navegador em `http://localhost:8501`. Se não abrir, acesse manualmente.

---

## Como usar a biblioteca no seu código

### Importação

```python
from dyntable import DynTable, DynType
```

Isso é tudo. O `__init__.py` expõe exatamente o que você precisa.

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

| Tipo              | Exemplo de valor    | Quando usar                        |
|-------------------|---------------------|------------------------------------|
| `DynType.STRING`  | `"sensor-01"`       | Textos, IDs, nomes                |
| `DynType.INT`     | `42`                | Contadores, versões, inteiros      |
| `DynType.FLOAT`   | `23.7`              | Temperatura, pressão, percentuais |
| `DynType.BOOL`    | `True` / `False`    | Estados, flags, interruptores     |
| `DynType.TIMESTAMP` | `time.time()`     | Datas e horários (Unix epoch)     |
| `DynType.BYTES`   | `b"\x01\x02"`       | Dados binários brutos             |
| `DynType.AUTO`    | (qualquer)          | Python detecta o tipo sozinho     |

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
row["temperatura"] = 25.0           # pelo objeto
tabela.set(row.id, "temperatura", 25.0)  # pelo ID
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

**Para arquivo CSV:**
```python
tabela.export_csv("dados.csv")
```

**Para string CSV (sem arquivo):**
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

## Tratamento de erros

A biblioteca usa **exceções** em vez de códigos de retorno (ao contrário da versão em C).

```python
from dyntable import (
    DynTable, DynType,
    ColumnNotFoundError,
    RowNotFoundError,
    DuplicateColumnError,
    TypeMismatchError,
    ColumnNameError,
)

tabela = DynTable("teste")
tabela.add_column("temp", DynType.FLOAT)

# Exemplo de tratamento
try:
    tabela.add_column("temp")         # coluna já existe!
except DuplicateColumnError as e:
    print(f"Erro: {e}")               # → Coluna 'temp' já existe.

try:
    tabela.get(row_id=999, col="temp")  # ID não existe
except RowNotFoundError as e:
    print(f"Erro: {e}")               # → Linha com ID 999 não encontrada.

try:
    row = tabela.new_row()
    row["temp"] = "vinte e três"      # string em coluna float!
except TypeMismatchError as e:
    print(f"Erro: {e}")
```

**Tabela de exceções:**

| Exceção               | Quando ocorre                                          |
|-----------------------|--------------------------------------------------------|
| `ColumnNotFoundError` | Tentar acessar coluna que não existe                  |
| `RowNotFoundError`    | Tentar acessar ID que não existe                      |
| `DuplicateColumnError`| Tentar adicionar coluna com nome já existente         |
| `TypeMismatchError`   | Inserir tipo incompatível em coluna com tipo fixo     |
| `ColumnNameError`     | Nome de coluna vazio ou maior que 64 caracteres       |

---

## Usando a interface web

Execute `streamlit run app.py` e use o painel:

- **Barra lateral → Nova coluna:** nome, tipo e se é nullable
- **Barra lateral → Nova linha:** campos aparecem dinamicamente para cada coluna
- **Aba Dados:** visualiza a tabela com filtro rápido e opção de deletar linhas
- **Aba Schema:** gerencia colunas (renomear, remover)
- **Aba Estatísticas:** min, max, média para colunas numéricas
- **Aba Exportar CSV:** baixa o arquivo ou visualiza o conteúdo

---

## Exemplo completo — cenário IoT real

```python
import time
from dyntable import DynTable, DynType

# Tabela começa com estrutura mínima
leituras = DynTable("leituras_fabrica")
leituras.add_column("sensor_id",  DynType.STRING, nullable=False)
leituras.add_column("lido_em",    DynType.TIMESTAMP)

# Sensor de temperatura se conecta
leituras.add_column("temp_c", DynType.FLOAT)
leituras.new_row(sensor_id="TMP-01", lido_em=time.time(), temp_c=45.2)

# Sensor de vibração se conecta (coluna nova em runtime)
leituras.add_column("vibracao_hz", DynType.FLOAT)
leituras.new_row(sensor_id="VIB-01", lido_em=time.time(), vibracao_hz=120.5)

# Sensor combinado
leituras.new_row(
    sensor_id="COMBO-01",
    lido_em=time.time(),
    temp_c=38.1,
    vibracao_hz=95.0
)

# Alerta: temperatura crítica
criticos = leituras.filter(temp_c=lambda v: v is not None and v > 40)
for r in criticos:
    print(f"ALERTA: {r['sensor_id']} está em {r['temp_c']} °C!")

print(leituras)
leituras.export_csv("fabrica.csv")
```

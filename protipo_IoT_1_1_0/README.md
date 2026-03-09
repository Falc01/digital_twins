# DynTable IoT — Documentação Completa

Tabela dinâmica em Python para projetos IoT: adicione colunas e linhas em qualquer momento, sem esquema fixo. Integração em tempo real com QGIS para visualização geoespacial.

---

## Estrutura do projeto

```
sua_pasta/
│
├── dyntable/               ← biblioteca principal
│   ├── __init__.py
│   ├── _types.py
│   └── _core.py
│
├── qgis_bridge/            ← integração com QGIS
│   ├── __init__.py
│   ├── layer_manager.py    → criar/recarregar camada IoT
│   ├── watcher.py          → QFileSystemWatcher + debounce
│   ├── project_manager.py  → criar/carregar .qgz
│   └── launcher.py         → subprocess (abre o QGIS)
│
├── dados/                  ← criada automaticamente
│   ├── sensor_readings.csv
│   ├── sensor_readings.schema.json
│   ├── projeto_iot.qgz     ← criado na primeira abertura do QGIS
│   └── basemap.tif         ← coloque aqui sua imagem de base
│
├── startup_script.py       ← injetado no QGIS via --code
├── app.py                  ← interface Streamlit
├── config.py               ← todas as configurações
├── table_manager.py        → gerenciador de múltiplas tabelas
├── setup_tabela.py
├── exemplo_iot.py
└── requirements.txt
```

> ⚠️ **Atenção:** Os arquivos `__init__.py`, `_types.py` e `_core.py` devem estar **dentro** da pasta `dyntable`. Os arquivos do `qgis_bridge` devem estar **dentro** da pasta `qgis_bridge`.

---

## Instalação (Windows)

> Todos os comandos abaixo são para o **terminal do VS Code** (`Ctrl + '`).
> Use `python`, não `python3` — no Windows o comando correto é `python`.

---

### Passo 1 — Confirmar que o Python está funcionando

```cmd
python --version
```

Deve aparecer algo como `Python 3.12.x`.

---

### Passo 2 — Entrar na pasta do projeto

```cmd
cd caminho\para\sua_pasta
```

---

### Passo 3 — Criar e ativar o ambiente virtual

```cmd
python -m venv .venv
```

**PowerShell:**
```powershell
.venv\Scripts\Activate.ps1
```

**Prompt de Comando:**
```cmd
.venv\Scripts\activate.bat
```

---

### Passo 4 — Instalar as dependências

```cmd
pip install -r requirements.txt
```

---

### Passo 5 — Criar a estrutura inicial da tabela

```cmd
python setup_tabela.py
```

---

### Passo 6 — Abrir a interface web

```cmd
streamlit run app.py
```

---

## Resolução de problemas comuns

### `python` não é reconhecido como comando

Adicione ao `Path` do Windows:
```
C:\Users\<seu_usuario>\AppData\Local\Programs\Python\Python312\
C:\Users\<seu_usuario>\AppData\Local\Programs\Python\Python312\Scripts\
```

### Erro `ModuleNotFoundError: No module named 'dyntable'`

Os arquivos estão soltos na raiz. Mova-os para dentro das subpastas corretas:
```cmd
mkdir dyntable
move __init__.py dyntable\
move _types.py dyntable\
move _core.py dyntable\
```

---

## Como usar a biblioteca no seu código

### Importação

```python
from dyntable import DynTable, DynType
```

### Criando uma tabela

```python
tabela = DynTable("sensor_readings")
```

### Adicionando colunas

```python
tabela.add_column("device_id",     DynType.STRING)
tabela.add_column("temperatura",   DynType.FLOAT)
tabela.add_column("porta_aberta",  DynType.BOOL)
tabela.add_column("registrado_em", DynType.TIMESTAMP)
tabela.add_column("pressao")   # tipo AUTO: inferido automaticamente
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

### Inserindo linhas

```python
row = tabela.new_row(
    device_id="sensor-T01",
    temperatura=23.7,
    registrado_em=time.time()
)
```

### Lendo valores

```python
temp = row["temperatura"]
temp = tabela.get(row_id=1, col="temperatura")
temp = tabela[1]["temperatura"]
```

### Filtrando linhas

```python
quentes = tabela.filter(temperatura=lambda v: v is not None and v > 25)
sensor  = tabela.find_one(device_id="sensor-T01")
```

### Estatísticas de coluna

```python
stats = tabela.column_stats("temperatura")
# {'count': 3, 'nulls': 2, 'min': 21.3, 'max': 23.7, 'avg': 22.1}
```

### Exportando dados

```python
tabela.export_csv("dados.csv")
csv_texto = tabela.to_csv_string()
registros = tabela.to_dicts()
```

---

## Persistência — salvar e carregar do disco

A persistência usa dois arquivos juntos:

```
dados/
  sensor_readings.csv             ← valores
  sensor_readings.schema.json     ← tipos, regras, próximo ID
```

```python
tabela.save("dados")
tabela = DynTable.load("dados", "sensor_readings")
tabela = DynTable.load_or_create("dados", "sensor_readings")
```

---

## Tratamento de erros

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

- **Barra lateral → Visualização GIS:** abre o QGIS sincronizado
- **Barra lateral → Nova coluna:** nome, tipo e se é nullable
- **Barra lateral → Nova linha:** campos aparecem dinamicamente
- **Aba Dados:** visualiza a tabela com filtro rápido
- **Aba Schema:** gerencia colunas (renomear, remover)
- **Aba Estatísticas:** min, max, média para colunas numéricas
- **Aba Exportar CSV:** baixa o arquivo ou visualiza o conteúdo

---

## QGIS Bridge — Sincronização em tempo real

O QGIS Bridge conecta o banco de dados IoT ao QGIS, mantendo o mapa atualizado automaticamente sempre que os dados mudam.

### Como funciona

```
Usuário edita dado no Streamlit
    → Streamlit salva CSV no disco
        → QFileSystemWatcher detecta a mudança
            → Debounce de 300ms (evita recargas múltiplas)
                → PyQGIS recarrega a camada de pontos
                    → Mapa atualiza preservando zoom e posição
```

Os dois processos (Streamlit e QGIS) são completamente independentes e se comunicam apenas pelo arquivo CSV no disco.

---

### Pré-requisitos para o QGIS Bridge

**1. QGIS 3.x instalado no Windows**

Baixe em [qgis.org](https://qgis.org/). Versão recomendada: QGIS 3.28 LTR ou mais recente.

**2. Colunas de coordenadas na tabela**

A tabela usada no QGIS precisa ter duas colunas com os nomes definidos em `config.py`:

```python
QGIS_LAT_COLUMN: str = "latitude"   # padrão
QGIS_LON_COLUMN: str = "longitude"  # padrão
```

Crie essas colunas no Streamlit antes de abrir o QGIS:

```
Barra lateral → Nova coluna → latitude  (FLOAT)
Barra lateral → Nova coluna → longitude (FLOAT)
```

**3. Imagem de base (opcional)**

Coloque um arquivo `basemap.tif` dentro da pasta `dados/`. Ele será carregado como camada raster na primeira abertura do QGIS. Se não existir, o QGIS abre sem basemap.

---

### Configuração em config.py

```python
# Caminho do executável do QGIS
# Se None, o sistema detecta automaticamente em C:\Program Files\QGIS*
QGIS_EXE_PATH: str | None = None

# Arquivo de projeto (.qgz) — criado automaticamente se não existir
QGIS_PROJECT_PATH: str = "dados/projeto_iot.qgz"

# Imagem de base
QGIS_BASEMAP_PATH: str = "dados/basemap.tif"

# Colunas de coordenadas
QGIS_LAT_COLUMN: str = "latitude"
QGIS_LON_COLUMN: str = "longitude"

# CRS (sistema de coordenadas) — padrão WGS84
QGIS_CRS: str = "EPSG:4326"
```

Se o QGIS não abrir automaticamente, edite `QGIS_EXE_PATH` com o caminho completo:
```python
QGIS_EXE_PATH = r"C:\Program Files\QGIS 3.34\bin\qgis-bin.exe"
```

---

### Abrindo o QGIS

Clique em **"🗺 Abrir no QGIS"** na barra lateral do Streamlit.

O que acontece:
1. O launcher localiza o `qgis-bin.exe`
2. Abre o QGIS com `startup_script.py` injetado via `--code`
3. Se o `projeto_iot.qgz` já existir, ele é carregado
4. Se não existir, é criado com o basemap e salvo
5. A camada de pontos IoT é carregada do CSV
6. O watcher inicia e fica monitorando o arquivo

A partir daí, qualquer inserção, edição ou deleção feita no Streamlit aparece no QGIS automaticamente em até 300ms.

---

### Estrutura dos módulos do bridge

| Arquivo                        | Roda em        | Responsabilidade                          |
|-------------------------------|----------------|-------------------------------------------|
| `qgis_bridge/launcher.py`     | Python normal  | Localiza QGIS e abre via subprocess       |
| `startup_script.py`           | Python do QGIS | Ponto de entrada — amarra tudo            |
| `qgis_bridge/project_manager.py` | Python do QGIS | Cria/carrega o arquivo .qgz            |
| `qgis_bridge/layer_manager.py`  | Python do QGIS | Recarrega camada preservando zoom        |
| `qgis_bridge/watcher.py`      | Python do QGIS | Monitora CSV com debounce                 |

---

### CRS e reprojeção

O CRS padrão é **EPSG:4326** (WGS84), que usa latitude e longitude em graus decimais. Se seus dados usam outro sistema de coordenadas (UTM, por exemplo), altere `QGIS_CRS` em `config.py` para o EPSG correspondente. O QGIS reprojetará automaticamente para o CRS do projeto ao exibir as camadas.

---

### Solução de problemas — QGIS Bridge

**QGIS não abre / executável não encontrado**

Edite `QGIS_EXE_PATH` em `config.py` com o caminho exato do seu QGIS:
```python
QGIS_EXE_PATH = r"C:\Program Files\QGIS 3.34\bin\qgis-bin.exe"
```

**Camada não aparece no QGIS**

Verifique se a tabela no Streamlit tem colunas com os nomes exatos definidos em `QGIS_LAT_COLUMN` e `QGIS_LON_COLUMN`, e se há linhas com valores válidos nessas colunas.

**O mapa não atualiza após editar dados**

O watcher monitora apenas o primeiro CSV encontrado na pasta `dados/` no momento em que o QGIS foi aberto. Se você criou uma nova tabela depois de abrir o QGIS, feche e reabra o QGIS pelo botão no Streamlit.

**Pontos aparecem em posição errada**

Confirme que os valores de latitude e longitude estão no formato correto para o CRS configurado. Para EPSG:4326, latitude deve estar entre -90 e 90 e longitude entre -180 e 180.

---

## Exemplo completo com coordenadas

```python
import time
from dyntable import DynTable, DynType

leituras = DynTable.load_or_create("dados", "sensores_campo")

if not leituras.col_count:
    leituras.add_column("sensor_id",  DynType.STRING, nullable=False)
    leituras.add_column("latitude",   DynType.FLOAT)
    leituras.add_column("longitude",  DynType.FLOAT)
    leituras.add_column("lido_em",    DynType.TIMESTAMP)
    leituras.add_column("temp_c",     DynType.FLOAT)

leituras.new_row(
    sensor_id="TMP-01",
    latitude=-12.9714,
    longitude=-38.5014,
    lido_em=time.time(),
    temp_c=32.4
)

leituras.save("dados")
# Abra o QGIS pelo Streamlit — o ponto aparecerá no mapa automaticamente
```

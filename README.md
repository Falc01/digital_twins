# DynTable IoT

Tabela dinâmica para projetos IoT: colunas e linhas criadas em runtime,
sem esquema fixo. Motor interno em matriz n×m (Python puro). Integração
em tempo real com QGIS. Interface web via Streamlit.

---

## Estrutura de pastas

```
projeto/
│
├── app.py                      ← boot do Streamlit (só config + despacho)
├── config.py                   ← todas as configurações (pasta, QGIS, limites)
├── table_manager.py            ← criar, listar, salvar, deletar tabelas
├── setup_tabela.py             ← roda 1× para criar estrutura inicial
├── exemplo_iot.py              ← exemplos de uso da biblioteca
├── startup_script.py           ← injetado no QGIS via --code
├── requirements.txt
│
├── dyntable/                   ← biblioteca de dados
│   ├── __init__.py
│   ├── _matrix.py              ← MatrixStore: grade n×m em Python puro
│   ├── _core.py                ← DynTable + DynRow (view sobre a matrix)
│   └── _types.py               ← DynType, DynCell, DynColumn, exceções
│
├── ui/                         ← camada de apresentação Streamlit
│   ├── __init__.py
│   ├── main.py                 ← render_app() e toda a lógica de UI
│   └── styles.py               ← CSS, type_badge(), TYPE_COLORS
│
├── qgis_bridge/                ← integração QGIS (só launcher roda fora)
│   ├── __init__.py
│   ├── launcher.py             ← abre o QGIS via subprocess
│   ├── project_manager.py      ← cria/carrega o .qgz     ⚠ roda no QGIS
│   ├── layer_manager.py        ← recarrega camada IoT     ⚠ roda no QGIS
│   └── watcher.py              ← QFileSystemWatcher       ⚠ roda no QGIS
│
└── dados/                      ← criada automaticamente
    ├── <tabela>.dyndb           ← pickle: matrix + schema + IDs (1 arquivo/tabela)
    ├── projeto_iot.qgz          ← criado na primeira abertura do QGIS
    └── basemap.tif              ← imagem de base para o mapa (opcional)
```

---

## Camadas e responsabilidades

```
app.py          →  boot: set_page_config + CSS + render_app()
  │
  ├─ ui/styles.py   →  CSS global e badges de tipo
  └─ ui/main.py     →  toda lógica Streamlit (abas, sidebar, estado)
       │
       ├─ config.py          →  constantes e caminhos
       └─ table_manager.py   →  gerencia arquivos .dyndb na pasta dados/
            │
            └─ dyntable/
                 ├─ _core.py     →  DynTable · DynRow (view sem cópia de dados)
                 ├─ _matrix.py   →  MatrixStore: list[list[Any]] n×m
                 └─ _types.py    →  tipos, células, colunas, exceções
                      │
                      └─ dados/*.dyndb   →  pickle binário (sem JSON separado)
```

---

## Instalação

```bash
# 1. Ambiente virtual
python -m venv .venv
.venv\Scripts\activate          # Windows PowerShell
# ou
source .venv/bin/activate       # Linux / macOS

# 2. Dependências
pip install -r requirements.txt

# 3. Criar tabela inicial
python setup_tabela.py

# 4. Abrir interface
streamlit run app.py

# 5. Interface HTML/CSS/JS
python web_app.py

Abra no navegador: http://127.0.0.1:8502
```

---

## Uso rápido

```python
from dyntable import DynTable, DynType

t = DynTable.load_or_create("dados", "leituras")

t.add_column("device_id",  DynType.STRING)
t.add_column("temperatura", DynType.FLOAT)

row = t.new_row(device_id="sensor-T01", temperatura=23.7)

print(t[row.id]["temperatura"])   # 23.7
print(t._store)                   # MatrixStore(1×2, cols=['device_id', 'temperatura'])

t.save("dados")                   # → dados/leituras.dyndb  (pickle, sem JSON)
```

---

## Formato de persistência

Cada tabela é um único arquivo `.dyndb` — um pickle do objeto `DynTable`
completo, incluindo a grade `n×m` (`MatrixStore`), os metadados de coluna
e os IDs de linha.

```
dados/
  leituras.dyndb          ← tabela "leituras"
  alertas.dyndb           ← tabela "alertas"
```

Não há CSV separado nem schema.json. O `TableManager` descobre as tabelas
listando os arquivos `*.dyndb` na pasta configurada.

---

## QGIS Bridge

O bridge conecta o banco ao QGIS para visualização geoespacial em tempo real.

```
Streamlit salva .dyndb
  → to_csv_string() exporta CSV temporário
    → QFileSystemWatcher detecta mudança (debounce 300 ms)
      → LayerManager recarrega camada preservando zoom
```

Abrir pelo botão **🗺 Abrir no QGIS** na barra lateral do Streamlit.
Configure o executável em `config.py` → `QGIS_EXE_PATH` se a detecção
automática falhar.

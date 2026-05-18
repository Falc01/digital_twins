# DynTable IoT 2.0.0

Uma biblioteca e ecossistema modular para gerenciamento de dados IoT com suporte a tabelas dinâmicas (sem esquema fixo) e integração geoespacial de alta performance com o QGIS.

Desenvolvido sob rígidas diretrizes de **Pure Python Core** (sem dependências pesadas como Pandas ou NumPy no núcleo) e **QGIS Isolation** (acoplamento fraco e reativo via Middleware).

---

## 🏗 Estrutura do Projeto

O projeto segue uma arquitetura limpa e orientada a domínios:

```
prototipo_IoT_2.0.0/
│
├── .gitignore                   ← Exclui arquivos gerados (.dyndb, .gpkg, .qgz)
├── requirements.txt             ← Dependências leves (Flask, openpyxl, etc.)
├── README.md
│
├── src/
│   ├── dyntable/                ← Core da Matriz Dinâmica (Pure Python)
│   │   ├── logic/
│   │   │   └── ingestors.py     ← Ingestor de planilhas Excel (Strategy Pattern)
│   │   └── data/
│   │       ├── _core.py         ← DynTable e DynRow (Views de dados)
│   │       ├── _matrix.py       ← MatrixStore (Estrutura de dados n×m)
│   │       └── _types.py        ← Sistema de tipos em runtime
│   │
│   ├── qgis/                    ← QGIS Bridge (Acoplamento Fraco)
│   │   ├── entry/
│   │   │   ├── launcher.py      ← Gerenciador de subprocesso do QGIS
│   │   │   └── startup_script.py ← Código Python injetado em runtime no QGIS
│   │   ├── logic/
│   │   │   ├── project_manager.py ← Setup e salvamento de projeto (.qgz)
│   │   │   └── watcher.py       ← Monitoramento de mudanças nos dados (.dyndb)
│   │   └── data/
│   │       ├── exporter.py      ← Exportador da DynTable para GeoPackage (.gpkg)
│   │       └── layer_manager.py ← Manipulador de camadas vetoriais
│   │
│   └── web/                     ← Backend Flask
│       └── entry/
│           └── web_app.py       ← Servidor e rotas da API REST
│
├── web_interface/               ← Frontend (Vanilla HTML, CSS, JavaScript)
│   ├── index.html               ← Painel de Controle e Upload
│   ├── styles.css               ← Interface moderna de alta estética
│   └── app.js                   ← Lógica assíncrona cliente
│
├── shared/
│   └── config.py                ← Configurações globais e caminhos absolutos
│
└── infra/dados/                 ← DataLake Local
    ├── dados_temperatura_salvador_pelourinho.xlsx ← Planilha de Carga
    └── pelourinho_recortado.tif  ← Basemap Raster do Pelourinho (EPSG:31984)
```

---

## ⚡ Camadas e Princípios Arquiteturais

### 1. Pure Python Core
A biblioteca `dyntable` armazena e manipula a matriz de dados utilizando exclusivamente as estruturas nativas do Python. Isso garante velocidade máxima de execução, portabilidade e elimina qualquer overhead de pacotes científicos pesados.

### 2. Ingestor Estratégico & Geolocalização Dinâmica
O `ExcelIngestor` realiza a carga de planilhas heterogêneas utilizando a biblioteca nativa `openpyxl`.
* **Carga Aditiva:** Colunas novas criam automaticamente novas dimensões na matriz dinâmica.
* **Espalhamento no Pelourinho:** Se a planilha não possuir dados de satélite, o ingestor automaticamente distribui os registros de forma alternada (Round-Robin) entre 5 coordenadas geográficas precisas localizadas dentro dos limites do raster `pelourinho_recortado.tif` (EPSG:31984).

### 3. Isolamento do QGIS (QGIS Isolation)
A ponte de integração não acopla o QGIS diretamente ao núcleo da aplicação. 
* O QGIS apenas "consome" os GeoPackages exportados.
* A sincronização em tempo real é feita de forma reativa: a interface salva em `.dyndb` (Pickle), o `watcher.py` (rodando no loop do QGIS) detecta o arquivo, recria o `.gpkg` local e atualiza a camada de exibição preservando a posição e zoom do usuário.

---

## 🚀 Como Executar o Projeto

### 1. Preparar o Ambiente
Crie um ambiente virtual e instale as dependências leves:
```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# ou
source .venv/bin/activate # Linux/macOS

pip install -r requirements.txt
```

### 2. Iniciar o Servidor Web
Rode o backend Flask:
```bash
python src/web/entry/web_app.py
```
O console exibirá o endereço `http://127.0.0.1:8502`.

### 3. Painel de Controle
* Acesse `http://127.0.0.1:8502` no navegador.
* Faça o upload da planilha contida em `infra/dados/dados_temperatura_salvador_pelourinho.xlsx`.
* Veja a matriz de dados ser populada instantaneamente.
* Clique em **"Abrir no QGIS"**. O lançador irá procurar o seu executável local do QGIS, gerar um projeto `.qgz` zerado, carregar o mapa base do Pelourinho e plotar os 5 sensores virtuais com todos os seus dados correlacionados!

# Resumo da Refatoração de Arquitetura (Digital Twin)

Este documento detalha as mudanças arquiteturais realizadas para migrar o projeto para a estrutura universal (`folder_arch` e `code_arch`) e solidificar o uso do padrão GeoPackage, removendo formatos obsoletos e centralizando responsabilidades.

## 1. Migração de Formatos (GeoPackage)

### Remoção de CSV e GeoJSON
* O sistema não utiliza mais nem cria arquivos `.csv` e `.geojson` na exportação de dados espaciais. Toda a pipeline de integração QGIS agora processa **exclusivamente GeoPackage (`.gpkg`)**.
* Arquivos `.csv` e `.geojson` legados que estavam poluindo a pasta `dados/` foram sumariamente deletados para evitar overhead ou uso acidental.
* As renderizações baseadas nesses arquivos antigos foram desligadas e o `layer_manager.py` agora aponta apenas para o driver do GeoPackage (OGR_GPKG).

## 2. Refatoração de Estrutura de Pastas

A organização base do repositório foi inteiramente reformulada visando o escalonamento do Twin Digital, dividindo domínios técnicos em suas próprias sub-redes:

### `infra/`
A camada de infraestrutura pura.
* `infra/dados/`: Anteriormente na raiz (`/dados/`). Todos os bancos de dados do sistema, incluindo os arquivos `.dyndb` de matriz e a exportação `.gpkg`, agora operam nativamente dessa pasta.

### `shared/`
Contém variáveis e utilitários globais.
* `shared/config.py`: Centraliza todos os PATHs da aplicação com resolução via caminhos absolutos atrelados à raiz. Isso impediu erros de carregamento que ocorriam dependendo de onde os scripts eram iniciados.

### `src/` (Módulos do Sistema)
O núcleo foi fragmentado em 3 domínios principais:

1. **`src/dyntable/`** (Responsável pelo Banco Customizado)
   * `data/`: Contém as lógicas de matriz e estruturas básicas como `_core.py`, `_matrix.py` e `_types.py`.
   * `logic/`: Agora contém o `table_manager.py` reescrito para referenciar a nova pasta de `infra/dados`.
2. **`src/qgis/`** (Antigo `qgis_bridge`)
   * `entry/`: Onde fica o ponto de partida do sistema QGIS: `startup_script.py` e o `launcher.py`.
   * `data/`: Modelos de dados e interações com o disco (como `exporter.py`, `layer_manager.py`, `gpkg_writer.py` e `models.py`).
   * `logic/`: Contém os controladores do projeto (`project_manager.py`, `watcher.py`, `pipeline.py` e `reader.py`).
     > *Nota de Refatoração:* O imenso `middleware.py` foi quebrado de acordo com os princípios **SOLID** em `gpkg_writer.py`, `models.py`, `pipeline.py` e `reader.py`. O código agora tem responsabilidades únicas claras (SRP).
3. **`src/web/`** (Antiga raiz / `ui`)
   * `entry/`: Contém o painel de inicialização local com `app.py` (Streamlit) e `web_app.py` (Flask).
   * `logic/`: Estilização e componentes de UI. O antigo `ui/main.py` foi desmembrado em componentes focados, incluindo `header.py`, `sidebar.py`, `tabs.py`, e `utils.py`.

## 3. Correções de Coordenadas (EPSG/QGIS)

Um problema crítico corrigido nesta versão foi o descasamento de reprojeção (**On-The-Fly / OTF**) do QGIS:
* A camada `.tif` (`EPSG:31984`) estava sendo forçada pelo nosso plugin para WGS84, o que fazia com que as posições ficassem desreguladas no mapa.
* Agora, a reprojeção é feita apenas na camada dos sensores do GeoPackage, à qual foi imposto explicitamente o `QgsCoordinateReferenceSystem('EPSG:4326')` no `layer_manager.py`. O QGIS entende o CRS de ambas e reposiciona os pontos com perfeição.

## 4. Testes e Setup

A lógica legada espalhada na raiz (`setup_tabela.py`, `exemplo_iot.py`) foi limpa.
* O `exemplo_iot.py` foi removido permanentemente, pois não servia de função à arquitetura principal.
* O script de recarregar matriz (`setup_tabela.py`) foi realocado para dentro do subdiretório `tests/` e atualizado para despejar a matriz em `infra/dados/`.
* Testes do `test_exporter.py` rodam normalmente validando que a tabela descarta arquivos corrompidos e preenche o `.gpkg`.

## Conclusão
O repositório do Digital Twin agora está pronto para implementações massivas, com módulos plug-and-play e caminhos resolvidos adequadamente. A ponte com o QGIS agora exige menos tempo de parse e exibe as coordenadas corretamente no Basemap.

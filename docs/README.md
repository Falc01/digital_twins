# 🧭 Guia Central de Navegação da Documentação
## Gêmeo Digital IoT — Centro Histórico do Pelourinho (UNIFACS)

Seja bem-vindo à documentação técnica oficial do projeto de Iniciação Científica em **Gêmeos Digitais IoT para Monitoramento Urbano e Fluxo de Pedestres** no Pelourinho, Salvador/BA.

A documentação adota o padrão **Docs-as-Code** estruturado sob o **Diátaxis Framework** (dividido em Tutoriais, Como-Fazer, Referência e Explicação), garantindo separação clara entre visão arquitetural, artigos teóricos e código-fonte.

---

## 🗺️ Mapa de Navegação Rápida

```text
docs/
├── README.md                      # [Você está aqui] Índice central de navegação
├── DEPLOY.md                      # Procedimentos de Deploy em Nuvem / OCI
├── project_overview.md            # Visão Executiva e Escopo do Gêmeo Digital
│
├── tutorials/                     # 📚 Tutoriais para Iniciantes (Aprenda Fazendo)
├── how-to/                        # 🛠️ Guias Práticos Passo a Passo (Como Resolver)
├── reference/                     # 📖 Dicionários de Dados & Variáveis de Ambiente
├── modules/                       # ⚙️ Especificação dos Microsserviços e Contêineres
├── adrs/                          # 🏛️ Architectural Decision Records (Decisões de Projeto)
│
├── explanation/                   # 🧠 Explicação Teórica, Arquitetura C4 e Dados Sintéticos
│   ├── arquitetura_c4.md          # Modelagem Arquitetural C4 do Sistema
│   ├── modelo_matematico_dados_sinteticos.md  # Artigo Científico Central & Bibliografia
│   ├── framework_unificado_dados_sinteticos.md # Consolidação Geral dos Trabalhos
│   └── dados_sinteticos/          # Suíte Canônica dos 6 Documentos Especializados (00 a 05)
│
├── logs_retorno/                  # 📋 Logs de Auditoria e Alinhamento com a Equipe
└── archive/                       # 📦 Camada Fria de Rascunhos Históricos Arquivados
```

---

## 🏛️ 1. Arquitetura do Sistema & Decisões de Projeto

O ecossistema é baseado em 5 contêineres Docker independentes orquestrados em topologia *Hub-and-Spoke* em torno do Datalake SQLite/GeoPackage:

* 📄 [**Visão Geral do Sistema**](explanation/visao_geral_sistema.md): Contexto urbano, atores e objetivos;
* 📄 [**Modelagem Arquitetural C4**](explanation/arquitetura_c4.md): Diagramas de Contexto, Contêineres e Componentes;
* 📄 [**ADR-001: QGIS Server Headless**](adrs/ADR-001_qgis_server_headless.md): Rationale para renderização cartográfica via OGC WMS/WFS;
* 📄 [**ADR-002: Topologia Hub-and-Spoke**](adrs/ADR-002_topologia_hub_and_spoke_datalake.md): Desacoplamento entre API, Watcher e GIS;
* 📄 [**ADR-003: Sincronização SQLite/GeoPackage**](adrs/ADR-003_sincronizacao_geopackage_sqlite.md): Estratégia de integridade e WAL mode;
* 📄 [**Deploy & Nuvem (OCI)**](DEPLOY.md): Manual de implantação em infraestrutura Oracle Cloud.

---

## 🧮 2. Motor de Dados Sintéticos & Simulação de Pedestres

O gerador de dados sintéticos simula a mobilidade urbana no Pelourinho através de modelos estocásticos em grafos e séries temporais, divididos rigorosamente em **Camada do Mundo Físico (Ground Truth)** e **Camada de Sensoriamento IoT**:

### Artigos Centrais e Fundamentação
* 📄 [**Artigo Metodológico Principal (modelo_matematico_dados_sinteticos.md)**](explanation/modelo_matematico_dados_sinteticos.md): Fundamentação teórica, equações mestras e **referências bibliográficas seminais com links diretos de acesso aberto** (González & Barabási, Borgers & Timmermans, Cameron & Trivedi, Weidmann);
* 📄 [**Framework Unificado de Dados Sintéticos**](explanation/framework_unificado_dados_sinteticos.md): Consolidação conceitual de toda a suíte.

### A Suíte Modular Especializada (Docs 00 a 05)
1. 📄 [**Doc 00: Arquitetura de Ingestão e Fluxo de Dados**](explanation/dados_sinteticos/00_arquitetura_ingestao_e_fluxo_dados.md): Barramento central e persistência no GeoPackage;
2. 📄 [**Doc 01: Macro-Fluxo Circadiano de Portões**](explanation/dados_sinteticos/01_entrada_saida_diaria.md): Influxo de pessoas nos portões de entrada física ($w_j$);
3. 📄 [**Doc 02: Injeção Dinâmica de Eventos**](explanation/dados_sinteticos/02_injecao_eventos.md): Surtos de público por atrações culturais e shows;
4. 📄 [**Doc 03: Circulação em Rede via Markov & Gravidade**](explanation/dados_sinteticos/03_circulacao_markov_pois.md): Caminhada entre ruas e praças, inércia de permanência e saída noturna nos portões (*egress*);
5. 📄 [**Doc 04: Saturação Física de Richards & Ruído IoT**](explanation/dados_sinteticos/04_saturacao_ruido_sensor.md): Camada de telemetria de hardware e ruído estocástico de Ornstein-Uhlenbeck;
6. 📄 [**Doc 05: Protocolos de Validação & Langevin**](explanation/dados_sinteticos/05_protocolos_validacao_langevin.md): Auditoria estatística (KS 2D / Divergência KL) e laboratório microscópico offline.

---

## 📋 3. Logs de Auditoria & Alinhamento com a Equipe (`logs_retorno/`)

Os logs registram especificações técnicas delegadas para a equipe de desenvolvimento:

* 🟡 [**Log Ativo — Módulo 01 (v2.0): Desacoplamento Urbano & Multimodalidade**](logs_retorno/log_retorno_doc01_v2_desacoplamento_e_multimodalidade.md): Especificação ativa em implementação pelo time;
* 📦 [**Arquivo de Logs Históricos (logs_retorno/archive/)**](logs_retorno/archive/): Registros e relatórios de resolução das versões anteriores já homologadas e resolvidas.

---

## 📚 4. Guias de Operação e Referência (Diátaxis)

* **Tutoriais:**
  * 📄 [01 - Primeiros Passos no Ecossistema](tutorials/01_primeiros_passos.md)
* **Guias Práticos (How-To):**
  * 📄 [Adicionar Novos Sensores no GeoPackage](how-to/adicionar_sensores.md)
  * 📄 [Configuração do Projeto QGIS Desktop](how-to/configuracao_qgis.md)
  * 📄 [Deploy na Nuvem Oracle (OCI)](how-to/deploy_oci.md)
* **Referência:**
  * 📄 [Dicionário de Dados do Sistema](reference/dicionario_dados.md)
  * 📄 [Variáveis de Ambiente (.env)](reference/variaveis_ambiente.md)
* **Catálogo de Módulos (`modules/`):**
  * Especificações técnicas de `dyntable_engine`, `fastapi_api`, `frontend`, `gpkg_exporter`, `nginx` e `qgis_server`.

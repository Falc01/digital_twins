# Roadmap de Desenvolvimento e Divisão de Tarefas: Gêmeo Digital IoT

Este documento apresenta uma sugestão prática de divisão de tarefas e cronograma de desenvolvimento para a equipe do projeto do Gêmeo Digital da UNIFACS, composta por 3 integrantes. 

A divisão foi pensada para manter os módulos isolados, respeitando a modularidade granular da arquitetura e permitindo o trabalho paralelo dos dois colegas, enquanto você assume o papel de **Integrador de Infraestrutura (DevOps) e QA (Garantia de Qualidade)**.

---

## 1. Distribuição de Responsabilidades (Papéis)

| Papel | Integrante | Escopo Geral |
| :--- | :--- | :--- |
| **Integrador / DevOps & QA** | **Você** | Configuração do Docker Compose, montagem dos volumes de disco compartilhados, integração de rede dos contêineres e validação de ponta a ponta. |
| **Desenvolvedor A (Backend & Dados)** | **Colega A** | Criação do `DataIngestor` geral, manipulação da matriz `.dyndb` e lógica de escrita do cache espacial no `.gpkg` (GeoPackage) e geração do `status.json`. |
| **Desenvolvedor B (Frontend & SIG)** | **Colega B** | Autoria do projeto de mapa `.qgs` no QGIS Desktop, estilização cartográfica e desenvolvimento da interface web interativa em Leaflet.js. |

---

## 2. Cronograma de Desenvolvimento (Etapas Lógicas)

O desenvolvimento deve ser realizado em **4 etapas sequenciais**, partindo da base de infraestrutura até o polimento visual.

### Etapa 1: Infraestrutura Base & Templates (A base de tudo)
O objetivo desta etapa é configurar o ambiente e os arquivos estáticos iniciais de design de mapa.

* **Sua Tarefa (Integrador):**
  * Criar a estrutura de diretórios do projeto.
  * Criar o arquivo `docker-compose.yml` inicial subindo os containers do **QGIS Server** e **FastAPI**, configurando o volume de disco compartilhado onde ficarão os arquivos `.gpkg` e `status.json`.
* **Colega A (Backend):**
  * Criar o esqueleto do projeto FastAPI em Python com as rotas básicas de saúde (`/health`) e a rota `/api/v1/status`.
* **Colega B (Frontend/SIG):**
  * Criar um banco GeoPackage (`.gpkg`) de exemplo com algumas geometrias fictícias de sensores (usando o QGIS Desktop).
  * Salvar o projeto `.qgs` associado a esse GeoPackage e disponibilizá-lo na pasta compartilhada da infraestrutura.

---

### Etapa 2: Desenvolvimento Isolado dos Módulos
Com a infraestrutura montada, os desenvolvedores de Backend e Frontend trabalham de forma 100% paralela.

* **Sua Tarefa (Integrador):**
  * Configurar a rota de proxy reverso ou o servidor estático que servirá a interface Leaflet para o usuário.
* **Colega A (Backend):**
  * Desenvolver o componente **`DataIngestor Geral`** (leitor genérico de arquivos de entrada como JSON e Excel) que escreve os registros na matriz `.dyndb`.
  * Criar a biblioteca de manipulação básica da matriz `.dyndb`.
* **Colega B (Frontend/SIG):**
  * Desenvolver a página HTML/CSS base do painel.
  * Implementar o mapa básico em JavaScript usando **Leaflet.js**, fazendo as chamadas `GetMap` (WMS) para o contêiner do QGIS Server usando as geometrias de exemplo criadas na Etapa 1.

---

### Etapa 3: Integração do Pipeline e Sincronização
O foco aqui é fazer o dado trafegar do backend até o banco de cache espacial.

* **Sua Tarefa (Integrador):**
  * Realizar a primeira integração de ponta a ponta: ligar o backend FastAPI ao mesmo volume físico que o QGIS Server consome, garantindo permissões de leitura/escrita corretas do Docker para o SQLite.
* **Colega A (Backend):**
  * Implementar o **FastAPI Adapter** que lê o `.dyndb`, traduz para coordenadas espaciais e atualiza o arquivo `.gpkg` em lote (Micro-batching simples de 30-60 min) usando o **Modo WAL** ativado no SQLite.
  * Fazer o FastAPI atualizar o arquivo `status.json` com o timestamp e status da gravação ao concluir a atualização.
* **Colega B (Frontend/SIG):**
  * Ajustar a estilização das camadas no projeto `.qgs` (ex: criar mapas de calor, definir gradientes de cores baseados em temperatura/umidade) usando o QGIS Desktop.
  * Exportar a versão final do `.qgs` para o volume de produção do QGIS Server.

---

### Etapa 4: UX Dinâmica e Validação Final (Polimento)
O fechamento do MVP com a comunicação de telemetria e testes de carga.

* **Colega A (Backend):**
  * Criar o endpoint HTTP `/api/v1/status` no FastAPI que abre o arquivo `status.json` do volume compartilhado e o retorna na resposta JSON para a web.
* **Colega B (Frontend/SIG):**
  * Implementar a rotina de **Auto-Introspecção** no Leaflet: consultar o WFS do QGIS Server e ler os atributos disponíveis dos sensores para desenhar os botões e filtros de variáveis na tela dinamicamente.
  * Implementar a chamada HTTP para `/api/v1/status` a cada intervalo de tempo e exibir a tag *"Última atualização às HH:MM"* no rodapé do mapa.
* **Sua Tarefa (Integrador - Validação Final):**
  * **Teste de Ponta a Ponta:** Enviar um novo payload de dados simulando um sensor via API Ingestora, aguardar o ciclo de sincronização e verificar se a geometria e a data de atualização mudam sozinhas no mapa do Leaflet.
  * Homologar o projeto e documentar a conclusão do MVP para a banca.

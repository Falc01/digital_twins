# Diário de Desenvolvimento e Solução de Problemas (Etapa 2 & Deploy)

Este documento registra todas as decisões de arquitetura, problemas de engenharia encontrados durante a modularização (Etapa 2) e o deploy (OCI Always Free) do Gêmeo Digital, detalhando as causas-raiz e as soluções técnicas implementadas.

---

## 1. Contexto e Objetivos da Etapa 2
* **Objetivo:** Remover a necessidade de abrir o QGIS Desktop no computador local para cadastrar e reposicionar sensores. 
* **Fluxo de Trabalho:** O usuário sobe uma planilha Excel/CSV no DataLake. Se a planilha não possuir coordenadas, os sensores entram em um painel lateral de "Sensores Pendentes". O usuário clica em "Definir Posição", clica em cima do mapa do Pelourinho, e a coordenada é persistida imediatamente, gerando a re-sincronização do GeoPackage (`.gpkg`) e do projeto cartográfico QGIS em segundo plano.

---

## 2. Problemas Encontrados no Backend/Frontend e Resoluções

### Problema 2.1: Erro 500 ao Carregar Tabelas Legadas (Deserialização Pickle)
* **Causa-raiz:** O backend legado salvava dados de metadados das tabelas dinâmicas utilizando a biblioteca `pickle` do Python na pasta `.dyndb`. Esses dados serializados gravavam a referência dos módulos antigos (`dyntable._core` e `dyntable.logic.ingestors`). Com a nossa refatoração e modularização do projeto, esses módulos foram movidos para novos caminhos estruturais (ex: `dyntable.data._core`). Ao tentar carregar tabelas do antigo datalake local, o Python gerava um erro `ModuleNotFoundError: No module named 'dyntable._core'`, quebrando a API com Erro 500.
* **Solução Implementada:** No arquivo [dyntable/__init__.py](file:///c:/Users/joaof/Downloads/Unifacs/digital_twins/backend/src/dyntable/__init__.py), injetamos mapeamentos dinâmicos no dicionário de módulos do sistema (`sys.modules`) no momento da importação. Mapeamos os caminhos legados para as novas classes correspondentes:
  ```python
  import sys
  from dyntable.data import _core
  sys.modules['dyntable._core'] = _core
  ```
  Isso garantiu compatibilidade de leitura retroativa automática (retro-compatibilidade) para todas as bases de dados e arquivos existentes sem perda de dados.

### Problema 2.2: Erro `ERR_CONNECTION_REFUSED` no Redirecionamento de Rotas do Nginx (Port-Stripping)
* **Causa-raiz:** O framework FastAPI realiza redirecionamentos automáticos HTTP 307 de rotas sem barra para rotas com barra no final (ex: `/api/v1/tables` ➡️ `/api/v1/tables/`). O proxy reverso do Nginx estava configurado com o cabeçalho padrão `Host $host` no repasse. O Nginx extrai a variável `$host` excluindo a porta. Como o projeto roda externamente na porta `8080` (atribuída no Docker Compose), o FastAPI gerava o cabeçalho `Location` de redirecionamento apontando para `http://localhost/api/v1/tables/` (na porta 80). Isso causava falhas de conexão recusada no navegador do usuário.
* **Solução Implementada:** No arquivo [nginx.conf](file:///c:/Users/joaof/Downloads/Unifacs/digital_twins/infra/docker/nginx.conf), alteramos a diretiva de cabeçalho do host do proxy para:
  ```nginx
  proxy_set_header Host $http_host;
  ```
  A variável `$http_host` preserva a porta de rede original (`8080`), permitindo que o FastAPI gerasse a URL de redirecionamento correta com a porta no sufixo.

### Problema 2.3: Log de Alerta Constante no Console do Navegador (Fallback WFS)
* **Causa-raiz:** O frontend tenta descobrir dinamicamente os atributos numéricos das tabelas consumindo o protocolo WFS (`DescribeFeatureType`) do QGIS Server. No entanto, se o projeto QGIS do servidor ainda não carregou a tabela nova (ou se a tabela está temporariamente vazia de feições), a resposta WFS retorna sem `featureTypes`. O frontend possuía um bloco `catch` no arquivo [app.js](file:///c:/Users/joaof/Downloads/Unifacs/digital_twins/frontend/js/app.js) que imprimia uma mensagem de aviso chamativa no console (`console.warn`) informando o uso de introspecção local. Esse log gerava spam constante e assustava os usuários.
* **Solução Implementada:** Como o mecanismo de **introspecção local** do frontend é robusto e se comporta exatamente como esperado na falta do WFS, nós removemos a linha de `console.warn` de dentro do bloco de exceção. A aplicação agora executa o fallback de forma silenciosa e limpa no console.

---

## 3. Problemas Encontrados na Nuvem (OCI) e Resoluções

### Problema 3.1: Sem Estoque de VMs Ampere (ARM) na OCI (Out of Capacity)
* **Causa-raiz:** As instâncias Ampere A1 (ARM, com até 24GB de RAM) são extremamente concorridas na região do data center de São Paulo (Always Free). O assistente de criação de VM da Oracle retornava o erro `Out of capacity for shape VM.Standard.A1.Flex`.
* **Solução Implementada:** Alteramos o formato da instância para a CPU clássica **AMD (VM.Standard.E2.1.Micro)**, que possui estoque permanente Always Free. Para compensar o limite estrito de **1 GB de RAM física** desse formato (já que nossa stack completa de 5 contêineres consome cerca de 1.2 GB), configuramos uma memória virtual de **4 GB de SWAP** no disco rígido do Ubuntu VPS. Isso expandiu a capacidade de paginação e evitou travamentos por estouro de RAM (Out Of Memory).

### Problema 3.2: Falha ao Obter IP Público da VM (Ausência de Sub-rede Pública)
* **Causa-raiz:** Em contas recém-criadas da Oracle Cloud, não existem redes VCN previamente configuradas. O assistente de criação da VM tentava gerar a rede interna, mas falhava silenciosamente ao não conseguir configurar um bloco CIDR livre, bloqueando a opção de atribuir um IP público para acesso SSH e web.
* **Solução Implementada:** Cancelamos o assistente manual de VM e usamos o **Assistente de VCN com Conectividade com a Internet (Set up a network with a wizard)**. Esse wizard automatizou a criação da VCN, do Internet Gateway e, principalmente, de uma sub-rede configurada como **pública** (`public subnet-vcn-project`). Depois, recriamos a VM apontando para essa sub-rede pública, liberando a geração do IP fixo.

### Problema 3.3: Conflitos de Modificação/Exclusão de Arquivos no Git (Modify/Delete)
* **Causa-raiz:** As ramificações de desenvolvimento (`dev-infra`, `dev-backend`, `dev-frontend`) possuíam commits que apagaram as pastas dos outros módulos para manter o "escopo exclusivo" das pastas. Quando tentamos atualizar essas branches usando a `main` integrada (`git merge main`), o Git identificava que os arquivos do backend haviam sido modificados na `main` mas deletados nas branches de desenvolvimento, gerando dezenas de conflitos de merge insolúveis de forma automatizada.
* **Solução Implementada:** Explicamos a arquitetura adequada de monorepo: branches em monorepos mantêm o código completo do projeto para garantir portabilidade e compilação independente, mas restringem a área de atuação nos commits. Para evitar overhead no momento de testes, optamos por **mesclar, consolidar e enviar todas as correções diretamente na branch `main`** do repositório público do GitHub, unificando as soluções.

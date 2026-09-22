# Guia de Refatoração e Melhorias do Frontend (Gêmeo Digital)

Este guia prático foi criado para orientar o desenvolvedor do frontend na reestruturação e refatoração do arquivo monolítico `Digital twins.html` (635 linhas), alinhando o código com as decisões de modularidade do projeto e preparando a interface para conexão com a API de produção em FastAPI e o QGIS Server.

---

## 1. Nova Estrutura de Arquivos (Modularização)

Para que o frontend atenda aos critérios de **modularidade granular**, o arquivo único `Digital twins.html` deve ser desmembrado em arquivos dedicados organizados na pasta `/frontend`:

```text
frontend/
├── index.html                   # Estrutura do Layout (Esqueleto HTML)
├── styles/
│   └── main.css                 # Estilos Cyberpunk, animações e variáveis CSS
└── js/
    ├── app.js                   # Ponto de entrada (Inicialização e loops)
    ├── api.js                   # Lógica de chamadas HTTP (Fetch/API REST)
    ├── map.js                   # Lógica do Leaflet, camadas base e WMS/WFS
    └── ui.js                    # Manipulação do DOM (Painéis, listas e sidebar)
```

### O que mover para cada arquivo:
* **`index.html`:** Mantenha apenas as tags HTML de layout estrutural (`<div id="tb">`, `<div id="sd">`, etc.), os links de CDN (Leaflet CSS/JS) e importe os arquivos JavaScript divididos ao final do `<body>` usando `<script type="module" src="js/app.js"></script>`.
* **`styles/main.css`:** Recorte todo o conteúdo que está dentro da tag `<style>` (linhas 10 a 390) e salve neste arquivo CSS dedicado.
* **`js/`:** Crie as subpastas e divida as funções JavaScript que estão embutidas nas linhas 400 a 633 de acordo com as seções abaixo.

> [!IMPORTANT]
> **Diferença Crucial: Construir a API (Backend) vs. Consumir a API (Frontend)**
> * **Backend (FastAPI - Colega A):** Responsável por programar as rotas físicas, conexões com o banco de dados `.dyndb`/`.gpkg` e regras de negócio no servidor. Ele cria a **"tomada"** (ex: `/api/v1/status`). O frontend não desenvolve ou executa esse código.
> * **Frontend (`js/api.js` - Colega B):** Responsável apenas por consumir as APIs. O arquivo `js/api.js` **não cria nenhuma rota ou banco de dados**; ele atua apenas como o **"cabo de conexão"** que dispara as requisições HTTP (`fetch`) para ler os dados do backend e do QGIS Server e entregá-los na tela do usuário.

---

## 2. Refatoração do Controle de Camadas (`togLayer`)

### O Problema Atual:
A alternância de camadas na função `togLayer(id)` utiliza blocos de `if` estáticos:
```javascript
if(id==='base'){...}
if(id==='sns'){...}
if(id==='heat'){...}
```
Isso causou dois erros:
1. **Ausência da Camada Grid:** O botão da **Grade Campus GPKG (`grid`)** está na tela, mas não funciona porque foi esquecido de criar um `if` para ele.
2. **Dependência de Código (Falta de Dinamicidade):** Toda vez que uma nova camada de mapa for inserida no QGIS, você precisará editar o JavaScript para adicionar um novo `if`.

### Solução Proposta (Substituir no seu `js/map.js`):
Crie um **dicionário dinâmico** para registrar as instâncias de camadas do Leaflet. Assim, a função `togLayer` busca a camada pelo ID sem precisar de nenhum bloco `if`:

```javascript
// 1. Dicionário de camadas (registradas no carregamento do mapa)
const activeLayers = {
  base: L.tileLayer('https://{s}.tile.openstreetmap.org/...'),
  sns: L.geoJSON(null, { ... }), // Sensores virtuais
  heat: L.heatLayer([], { ... }), // Mapa de calor
  grid: L.tileLayer.wms('http://localhost:8080/wms', { layers: 'grade_campus', ... }) // Grade do QGIS
};

// 2. Função toggle unificada e dinâmica (sem ifs)
function togLayer(id) {
  const layer = activeLayers[id];
  
  if (!layer) {
    console.warn(`A camada com ID "${id}" não foi inicializada no mapa.`);
    return;
  }

  // Alterna a camada no mapa de forma genérica
  if (map.hasLayer(layer)) {
    map.removeLayer(layer);
  } else {
    map.addLayer(layer);
  }
}
```

---

## 3. Remoção de Mocks e Substituição por Chamadas HTTP Assíncronas

Na refatoração, todos os dados estáticos simulados no arquivo atual devem ser removidos e substituídos por requisições de rede assíncronas reais voltadas para a API FastAPI.

> [!WARNING]
> **O Frontend não lê o Datalake diretamente:** Lembre-se de que o navegador do usuário final (onde o Leaflet roda) não tem acesso físico aos arquivos do servidor (`.dyndb` ou `.gpkg`). Toda comunicação de dados tabulares ou status deve ser feita exclusivamente via chamadas de rede HTTP REST para a API FastAPI.

### A. Mocks que devem ser Removidos
No código atual do `Digital twins.html`, remova completamente os dados estáticos que estão declarados de forma fixa na tag `<script>`:
* **`STATUS_JSON`:** Objeto mockado com o timestamp estático e status de sucesso.
* **`SENSORS`:** Array de dados estáticos que simula a posição e o estado dos sensores no campus.

### B. Implementação da Telemetria de Sincronia (`/api/v1/status`)
O FastAPI grava dados no GeoPackage a cada 30-60 minutos usando o modo WAL do SQLite. Para exibir no rodapé do mapa o horário exato da última sincronia realizada pelo servidor, substitua o mock `loadStatus()` por uma chamada HTTP real em `js/api.js` e `js/ui.js`:

```javascript
// js/api.js ou js/ui.js
async function loadStatus() {
  try {
    // 1. Dispara requisição HTTP GET para a rota de telemetria da API FastAPI
    const response = await fetch('/api/v1/status');
    if (!response.ok) throw new Error('Falha ao conectar na API de status.');
    
    const statusData = await response.json(); // Retorna: { ultima_atualizacao: "...", status: "..." }
    
    // 2. Atualiza os elementos da barra de status no rodapé do HTML
    document.getElementById('sync-ts').textContent = statusData.ultima_atualizacao;
    
    const statusEl = document.getElementById('sync-s');
    statusEl.textContent = statusData.status;
    statusEl.style.color = statusData.status === 'sucesso' ? 'var(--gn)' : 'var(--rd)';
  } catch (error) {
    console.error('Erro de conexão com o backend:', error);
    document.getElementById('sync-s').textContent = 'Erro de Conexão';
    document.getElementById('sync-s').style.color = 'var(--rd)';
  }
}
```

### C. Busca Dinâmica dos Sensores (`/api/v1/sensors`)
Substitua o carregamento estático do array `SENSORS` por uma chamada que busca a lista de sensores atualizada diretamente da API backend do FastAPI:

```javascript
// js/api.js
export async function getSensorsFromAPI() {
  try {
    const response = await fetch('/api/v1/sensors');
    if (!response.ok) throw new Error('Falha ao obter dados dos sensores da API.');
    return await response.json(); // Retorna a lista real de feições/sensores
  } catch (error) {
    console.error('Erro ao conectar na API de sensores:', error);
    return []; // Retorna lista vazia em caso de falha de conexão
  }
}
```

---

## 4. Auto-Introspecção via WFS (Zero-Code)

### O Problema do Acoplamento:
Atualmente, o frontend autodescobre quais variáveis/atributos os sensores possuem (temperatura, umidade, co2) inspecionando diretamente as chaves do objeto de sensores retornado pela API REST (`Object.keys(SENSORS[0].data)`). 

Se o formato de resposta da API do FastAPI mudar ou se quisermos plotar dados que vêm diretamente do servidor de mapas, esse método pode quebrar.

### A Solução por Projeto:
A autodescoberta do esquema de variáveis deve ser delegada ao **QGIS Server** utilizando o protocolo **WFS (Web Feature Service)**. 
* O frontend realiza uma chamada HTTP do tipo `GetCapabilities` ou `DescribeFeatureType` para a URL do QGIS Server.
* O QGIS Server devolve um esquema XML/JSON descrevendo a tabela de atributos da camada.
* O JavaScript do frontend realiza o parse desse retorno e monta dinamicamente os botões de seleção de atributos na tela.
* Isso garante que o frontend permaneça cego em relação a como o banco de dados armazena os dados, utilizando o QGIS Server como a única fonte de verdade geoespacial.

> [!TIP]
> A chamada WFS para descobrir as propriedades de uma camada possui a seguinte estrutura de URL padrão:
> `http://qgis-server/wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=DescribeFeatureType&OUTPUTFORMAT=application/json&TYPENAME=sensores`

---

## 5. Resumo de Tarefas para o Frontend (Checklist)

Para facilitar a organização da sua Sprint de refatoração, siga esta ordem de tarefas:

* [ ] **Desmembrar arquivos:** Recortar folhas de estilo e funções JavaScript do `Digital twins.html` para as pastas de destino.
* [ ] **Criar o Dicionário `activeLayers`:** Registrar as camadas do mapa de forma dinâmica e remover os múltiplos `if`s da função `togLayer`.
* [ ] **Mapear a camada `'grid'`:** Ligar a lógica de toggle do botão da grade no mapa Leaflet.
* [ ] **Implementar requisição do endpoint `/api/v1/status`:** Substituir o mock por chamadas `fetch` assíncronas reais.
* [ ] **Implementar autodescoberta via WFS:** Trocar a leitura direta de chaves JSON pela consulta HTTP `DescribeFeatureType` ao QGIS Server.

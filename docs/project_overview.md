# Visão Geral do Gêmeo Digital: Arquitetura de Mapas

Este documento apresenta uma visão conceitual de alto nível sobre a arquitetura de visualização geoespacial do Gêmeo Digital da UNIFACS, comparando abordagens de implementação e propondo um modelo escalável, modular e otimizado para o ecossistema do projeto.

---

## 1. QGIS Desktop vs. QGIS Server: Entendendo as Diferenças

Para planejar a infraestrutura de forma correta, é preciso compreender que o QGIS Desktop e o QGIS Server são ferramentas distintas projetadas para propósitos diferentes:

| Aspecto | QGIS Desktop | QGIS Server |
| :--- | :--- | :--- |
| **Interface** | Interface gráfica de usuário (GUI) completa com menus, botões e janelas visuais. | Sem interface gráfica (headless). Executa de forma invisível em segundo plano. |
| **Objetivo Principal** | Autoria, design cartográfico, análise espacial complexa e edição manual de mapas. | Publicação de mapas na Web, servindo dados e renderizando imagens sob demanda. |
| **Público-Target** | Engenheiros, cartógrafos, geógrafos e analistas de dados. | Aplicações Web, sistemas integrados e navegadores dos usuários finais. |
| **Protocolo de Uso** | Cliques manuais e comandos interativos na máquina local do designer. | Requisições HTTP padronizadas (protocolos WMS e WFS da OGC). |

* **Conclusão Neutra:** O QGIS Desktop é uma ferramenta local para criação e design visual. O QGIS Server é um motor headless automatizado voltado para servir mapas na web sob demanda.

---

## 2. Os Desafios de Rodar o QGIS Desktop em Kubernetes

Propor que os operadores acessem e manipulem o mapa através de instâncias do QGIS Desktop rodando dentro de containers em um cluster Kubernetes apresenta desafios práticos significativos de engenharia de infraestrutura:

* **Consumo de Recursos (Densidade):** Por carregar toda a interface gráfica de desktop, gerenciamento de janelas e dependências pesadas, cada container consome cerca de 1.5 GB a 2 GB de RAM. Em larga escala (múltiplos operadores simulando), isso gera alto custo de nuvem.
* **Complexidade de Concorrência:** O projeto do QGIS (`.qgz`/`.qgs`) é estruturado como um arquivo estático único. Se múltiplos usuários tentarem editá-lo simultaneamente no servidor, as alterações de um sobrescreverão as dos outros, resultando em perda de dados.
* **Transmissão de Interface (VNC/Streaming):** Fazer streaming de vídeo de um software desktop para o navegador web exige grande largura de banda de rede e introduz latência perceptível nos cliques do usuário.

---

## 3. A Proposta de Solução: Arquitetura Modular em Containers (Docker)

Para eliminar a dependência de interfaces gráficas pesadas no servidor, propõe-se uma arquitetura baseada em microsserviços integrados de forma transparente via Docker:

```
[ Ingestão / Dispositivos ] ──► [ Matriz .dyndb ] ──► [ FastAPI Adapter ]
                                                            │
                                             ┌──────────────┴──────────────┐
                                             ▼ (Gravação Otimizada)        ▼ (Escreve Timestamp)
[ Web Client (Leaflet) ] ◄──(Serviço WMS)── [ QGIS Server ] ◄─────────── [ Volumes (.gpkg / status.json) ]
```

1. **Geração Automática do Projeto:** O arquivo de design do mapa (`.qgs`) é configurado uma única vez. As regras de atualização de dados e estilos ocorrem de forma transparente nas tabelas em segundo plano, sem intervenção humana no servidor.
2. **QGIS Server Headless:** Funciona em container dedicado, consumindo dados geográficos locais e servindo imagens PNG sob demanda para a interface web.
3. **Controle Dinâmico na Web:** O usuário final interage com um painel web interativo leve. Suas ações são traduzidas em requisições web para o servidor, garantindo isolamento de sessão e alta performance.

---

## 4. A Modularidade Granular: Topologia Estrela (Hub-and-Spoke)

Para garantir desacoplamento total, o ecossistema adota a topologia em **Estrela**. Os contêineres não dependem do funcionamento direto uns dos outros em cascata; em vez disso, todos orbitam de forma independente um **Datalake Central** (volume de disco compartilhado no Docker):

```
         ┌───────────────────────────┐
         │    DataIngestor Geral     │
         │   (Excel / JSON / IoT)    │
         └─────────────┬─────────────┘
                       │ Grava
                       ▼
         ┌───────────────────────────┐
         │     DATALAKE CENTRAL      │◄─────┐
         │ (.dyndb, .gpkg, status)   │      │
         └──────┬──────────────┬─────┘      │
                │              │            │ Sincroniza
                │ Lê           │ Lê         │
                ▼              ▼            │
         ┌──────────────┐    ┌──────────────┴─┐
         │ QGIS Server  │    │ FastAPI API    │
         │  (Headless)  │    │  (Backend)     │
         └──────▲───────┘    └──────▲─────────┘
                │                   │
                │ HTTP (WMS/WFS)    │ HTTP (REST/JSON)
                │                   │
         ┌──────┴───────────────────┴─────────┐
         │       INTERFACE WEB CLIENT         │
         │    (HTML5 / CSS3 / Leaflet.js)     │
         └────────────────────────────────────┘
```

Esta quebra de acoplamento cria uma **Modularidade Granular**, permitindo que cada peça do Lego seja atualizada sem derrubar o resto do sistema:
* **Ingestor Geral:** Processa qualquer formato de entrada e grava no `.dyndb`. Se novas fontes IoT surgirem, o resto do mapa permanece intacto.
* **FastAPI (Adaptador):** O único componente que entende a matriz `.dyndb`. Ele traduz os dados dinâmicos para a "caixa postal" (o GeoPackage `.gpkg`). Se o banco de dados principal mudar no futuro, apenas este adaptador é modificado.
* **QGIS Server:** Consome localmente o GeoPackage e responde a requisições WMS. Se ele falhar, a API FastAPI continua recebendo dados IoT normalmente, e os gráficos tabulares da interface continuam funcionando.
* **Web Client (Leaflet):** Um painel web ultra-leve focado apenas em renderizar a tela. Ele se comunica via HTTP com o QGIS Server para obter imagens de mapas e com o FastAPI para obter dados tabulares e status de sincronização, sem nunca acessar o Datalake diretamente.

---

## 5. Definição de Mapas Dinâmicos e Concorrência Segura

A dinamicidade e a concorrência na exibição de dados em tempo real são resolvidas por meio de três pilares de engenharia:

### A. O que torna o mapa "Dinâmico"?
1. **Dados Vivos:** As atualizações na matriz `.dyndb` são sincronizadas periodicamente pelo FastAPI no GeoPackage, mantendo os dados cartográficos frescos.
2. **Estilização Paramétrica:** O Web Client altera a simbologia (como mapas de calor ou faixas de cores) enviando parâmetros simples nas consultas HTTP (WMS/WFS). O QGIS Server renderiza o estilo dinamicamente em memória em milissegundos.
3. **Auto-Introspecção (Zero-Code):** O frontend lê os dados dos sensores no carregamento da tela e autodescobre as novas variáveis de sensores (como temperatura, umidade, co2), gerando botões e controles automaticamente sem alterações de código.

### B. Prevenção de Conflitos e Travamento de Arquivo (Locks)
Como o GeoPackage (`.gpkg`) usa um banco SQLite de arquivo único sob o capô, a concorrência de acessos em escrita e leitura simultâneas é tratada de forma muito simples no projeto:

1. **Sincronização Periódica Programada (30 a 60 min):** Como a atualização dos dados do Gêmeo Digital ocorre em intervalos longos de meia hora a uma hora, o FastAPI gasta apenas alguns segundos escrevendo os dados novos no disco. Durante os outros 29 ou 59 minutos do ciclo, o arquivo do GeoPackage fica inteiramente livre e sem concorrência para a leitura rápida do QGIS Server.
2. **Modo WAL (Write-Ahead Logging):** Mantido ativo no banco de cache espacial para que as leituras do QGIS Server e a escrita periódica do FastAPI ocorram de forma simultânea e paralela, blindando o MVP contra o travamento do arquivo.
3. **Telemetria de Atualização (status.json):** Ao concluir a gravação de dados, o FastAPI grava um pequeno arquivo estático `status.json` com o horário da última execução no volume Docker. Para que o frontend (rodando no navegador do usuário) saiba disso, ele faz uma consulta HTTP rápida ao FastAPI, que lê o arquivo local do disco e devolve as informações. O frontend exibe de forma simples uma mensagem informativa como *"Dados atualizados em: 22/05/2026 20:00"*, fornecendo transparência ao usuário final sobre a integridade dos dados sem a necessidade de requisições complexas no banco de dados.

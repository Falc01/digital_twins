# 🚀 Tutorial: Primeiros Passos com o Gêmeo Digital IoT

Este tutorial orienta o desenvolvedor ou pesquisador do zero até a execução completa da stack do **Gêmeo Digital IoT da UNIFACS (Pelourinho, Salvador/BA)** em sua máquina local.

---

## 🎯 Objetivos do Tutorial
Ao final desta lição, você será capaz de:
1. Clonar o repositório e preparar o ambiente local com Docker Compose.
2. Subir os 5 microsserviços integrados da aplicação.
3. Realizar a ingestão do primeiro conjunto de dados de sensores IoT.
4. Visualizar o mapa cartográfico interativo no navegador web.

---

## 📋 Pré-requisitos
Antes de começar, certifique-se de ter instalado em sua máquina:
* **Git**: [Instalar Git](https://git-scm.com/)
* **Docker Desktop** (com suporte a Docker Compose): [Instalar Docker](https://www.docker.com/)
* Navegador Web moderno (Google Chrome, Firefox ou Microsoft Edge).

---

## 🛠️ Passo 1: Obter o Código Fonte

Abra o seu terminal (Bash, PowerShell ou Zsh) e execute:

```bash
git clone https://github.com/Falc01/digital_twins.git
cd digital_twins
```

---

## 🐳 Passo 2: Inicializar a Stack de Contêineres

Suba os serviços definidos no `docker-compose.yml`:

```bash
docker compose up -d
```

> [!NOTE]
> Na primeira execução, o Docker fará o download das imagens do QGIS Server, Python FastAPI e Nginx. Isso pode levar alguns minutos.

Para verificar se todos os 5 contêineres estão ativos:

```bash
docker compose ps
```

Deverão constar os serviços:
* `nginx_gateway` (Porta 8080)
* `fastapi_api` (Porta 8000 interna)
* `frontend_web` (Porta 80 interna)
* `qgis_server` (Porta 8081 interna)
* `qgis_watcher` (Daemon de sincronização)

---

## 🌐 Passo 3: Acessar a Interface Web

Abra o navegador e acesse:

👉 **[http://localhost:8080](http://localhost:8080)**

Você verá o painel interativo do Gêmeo Digital carregando o mapa base do Pelourinho (Salvador/BA) com as camadas Leaflet e QGIS Server.

---

## 📊 Passo 4: Realizar a Ingestão de Dados IoT

1. Acesse o **Portal de Upload** em: [http://localhost:8080/upload.html](http://localhost:8080/upload.html)
2. Faça o upload de um arquivo de teste em formato CSV ou Excel (localizados na pasta de exemplos ou backend).
3. Clique em **Enviar e Ingerir**.
4. O sistema irá:
   - Cadastrar os sensores e leituras na matriz `.dyndb` / SQLite.
   - Sincronizar as coordenadas no GeoPackage (`.gpkg`).
   - Notificar o QGIS Server para atualizar a camada espacial.
5. Volte para o mapa principal ([http://localhost:8080](http://localhost:8080)) e observe a marcação dos sensores atualizada em tempo real!

---

## 🛑 Passo 5: Parar os Serviços

Para encerrar a execução da stack e liberar os recursos:

```bash
docker compose down
```

---

## 🎓 Próximos Passos
Agora que você domina a execução básica, consulte:
* 📖 **[Guia de Deploy em Produção (OCI)](../how-to/deploy_oci.md)**: Como implantar na nuvem Oracle.
* 🛠️ **[Como Adicionar Novos Sensores](../how-to/adicionar_sensores.md)**: Como estender o modelo para novos tipos de telemetria.
* 🏛️ **[Visão de Arquitetura C4](../explanation/arquitetura_c4.md)**: Para entender a topologia Hub-and-Spoke.

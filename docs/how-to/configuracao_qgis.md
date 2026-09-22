# 🛠️ Guia Prático: Configuração e Estilização do QGIS Server Headless

Este guia orienta engenheiros e cartógrafos na criação e ajuste de estilos cartográficos, projetos QGIS (`.qgz`/`.qgs`) e serviços OGC (WMS/WFS) consumidos pelo Gêmeo Digital.

---

## 🗺️ Visão Geral do Fluxo QGIS

No ecossistema do Gêmeo Digital, o **QGIS Server** roda em contêiner Docker sem interface gráfica (*headless*). Ele lê o arquivo GeoPackage (`/infra/dados/digital_twin.gpkg`) e serve requisições OGC WMS (imagens PNG de mapas) e WFS (feições vetoriais GeoJSON) para a interface web.

---

## 🎨 1. Criar e Editar Projetos no QGIS Desktop

1. Abra o **QGIS Desktop** em sua máquina de desenvolvimento local.
2. Adicione a camada vetorial apontando para o arquivo GeoPackage `digital_twin.gpkg`.
3. Configure as propriedades da camada:
   - **Simbologia:** Defina cores, tamanhos de marcadores, gradientes ou renderizador de Mapa de Calor (*Heatmap*).
   - **Rótulos (Labels):** Ative a exibição dos IDs dos sensores ou valores de telemetria.
   - **Propriedades WMS/WFS:** Em **Projeto > Propriedades do Projeto > QGIS Server**, marque as caixas para publicar as camadas via WMS/WFS e selecione os campos expostos.
4. Salve o projeto como `pelourinho_map.qgz` na pasta `infra/dados/`.

---

## 🔄 2. Sincronização e Watcher Daemon

O contêiner `qgis_watcher` monitora alterações no banco de dados e no arquivo de projeto:
- Quando o backend insere novos sensores no GeoPackage, o watcher invalida e regenera as regras do arquivo `.qgz` em background sem derrubar o servidor.
- Para forçar o recarregamento imediato das camadas no servidor via API:

```bash
curl -X POST "http://localhost:8080/api/v1/qgis/reload"
```

---

## 🧪 3. Testar Serviços OGC WMS / WFS Localmente

Você pode testar se o QGIS Server está respondendo corretamente usando requisições WMS `GetCapabilities` ou `GetMap` diretamente no navegador ou terminal:

### Teste GetCapabilities (WMS):
```
http://localhost:8080/qgis?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities
```

### Teste GetMap (Renderizar Imagem PNG do Mapa):
```
http://localhost:8080/qgis?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=sensores_iot&STYLES=&CRS=EPSG:4326&BBOX=-12.98,-38.52,-12.96,-38.50&WIDTH=800&HEIGHT=600&FORMAT=image/png
```

Se o XML de resposta ou a imagem PNG forem exibidos corretamente, o QGIS Server está operando perfeitamente!

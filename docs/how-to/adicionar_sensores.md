# 🛠️ Guia Prático: Como Ingerir Dados e Adicionar Novos Sensores IoT

Este guia descreve como adicionar novos sensores, registrar variáveis de telemetria e ingerir planilhas de dados no ecossistema do **Gêmeo Digital IoT**.

---

## 🎯 Formatos de Arquivo Suportados
O módulo de ingestão (`fastapi_api` / `dyntable_engine`) aceita arquivos nos formatos:
- **CSV (`.csv`)**: Separado por vírgulas ou ponto-e-vírgula, com codificação UTF-8.
- **Excel (`.xlsx`, `.xls`)**: Planilhas padrão com cabeçalhos na primeira linha.

---

## 📋 Estrutura da Planilha de Ingestão

Para que a ingestão automática funcione sem erros, a planilha deve conter obrigatoriamente as seguintes colunas de cabeçalho:

| Nome da Coluna | Tipo | Obrigatório | Descrição / Exemplo |
| :--- | :--- | :--- | :--- |
| `sensor_id` | Texto | **SIM** | Identificador único do sensor (ex: `TEMP_PELO_01`). |
| `latitude` | Numérico (float) | **SIM** | Coordenada em graus decimais WGS84 (ex: `-12.9714`). |
| `longitude` | Numérico (float) | **SIM** | Coordenada em graus decimais WGS84 (ex: `-38.5123`). |
| `timestamp` | Datetime / Texto | **SIM** | Data/Hora da leitura (ex: `2026-08-13 14:30:00`). |
| `[variavel_telemetria]` | Numérico / Texto | Não | Qualquer variável IoT (ex: `temperatura`, `umidade`, `co2`, `ruido`). |

---

## 📥 Métodos de Ingestão

### Método 1: Via Interface Web (Portal de Ingestão)
1. Acesse o portal em `http://localhost:8080/upload.html` (ou a URL de produção na OCI).
2. Arraste e solte o arquivo CSV/Excel ou clique em **Selecionar Arquivo**.
3. Defina o nome da nova tabela dinâmica (ex: `telemetria_pelourinho_2026`).
4. Clique em **Enviar e Ingerir**.
5. O sistema atualizará automaticamente os marcadores Leaflet e as camadas QGIS.

### Método 2: Via API REST (cURL / Python)
Você pode automatizar a ingestão assíncrona enviando uma requisição `POST` com o arquivo multipart para o backend:

```bash
curl -X POST "http://localhost:8080/api/v1/ingest" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@caminho/para/seus_dados.csv" \
     -F "table_name=leituras_sensores_novos"
```

---

## 🔍 Como o Sistema Trata Novos Atributos (Auto-Introspecção)
O frontend Leaflet e a API possuem um mecanismo de **Zero-Code Auto-Discovery**:
1. Se você adicionar uma nova coluna como `qualidade_ar` ou `pressao_hpa`, o backend registra o novo tipo na tabela `.dyndb` e atualiza a matriz de atributos.
2. O GeoPackage (`.gpkg`) recebe os novos campos na tabela espacial.
3. O painel web identifica os novos atributos e cria seletores dinâmicos no dashboard cartográfico sem necessidade de alterar o código do sistema!

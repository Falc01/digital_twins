# 📦 Especificação Técnica: Gateway Nginx (`infraestrutura_gateway_nginx`)

## 1. 🎯 Resumo Executivo & Responsabilidade Única
O módulo **`infraestrutura_gateway_nginx`** é a porta de entrada pública e o roteador de tráfego do sistema Gêmeo Digital (`infra/docker/nginx.conf`). Sua **responsabilidade única** é atuar como um **Reverse Proxy (Proxy Reverso)** de alta performance na porta pública `8080`, roteando de forma transparente as requisições HTTP recebidas para os seus respectivos serviços internos (Frontend, API FastAPI e QGIS Server) e garantindo a preservação de portas em redirecionamentos.

---

## 2. 📊 Arquitetura Visual & Diagrama de Sequência (Mermaid)

```mermaid
graph TD
    Client[Navegador / Cliente Externo] -->|HTTP Porta 8080| Nginx[Nginx Gateway Container]
    
    subgraph Rede Interna Docker (digital_twins_net)
        Nginx -->|/ (Rota Raiz)| Frontend[gd-frontend:3000]
        Nginx -->|/api/| Backend[gd-backend:8000]
        Nginx -->|/qgis| QGIS[gd-qgis-server:80]
    end
```

---

## 3. 📋 Análise de Requisitos (RFs e RNFs com ID)

| ID | Tipo | Descrição do Requisito | Critério de Aceite |
| :--- | :--- | :--- | :--- |
| **RF-NGX-01** | Funcional | Roteamento de tráfego baseado na URI da requisição. | Redirecionar `/` para o frontend, `/api` para o backend e `/qgis` para o servidor GIS. |
| **RF-NGX-02** | Funcional | Preservação de cabeçalhos HTTP de host e porta externa. | Utilizar `proxy_set_header Host $http_host` para impedir a perda da porta 8080 em redirecionamentos 307. |
| **RNF-NGX-01**| Segurança | Ocultar portas e topologia de rede interna dos serviços. | Não expor as portas internas (3000, 8000) diretamente para a internet. |
| **RNF-NGX-02**| Desempenho| Baixo overhead e consumo mínimo de recursos de CPU/RAM. | Utilizar a imagem otimizada `nginx:alpine` rodando com menos de 15MB de RAM. |

---

## 4. 🔑 Dicionário de Variáveis, Atributos & Tipagem de Dados

| Atributo / Configuração | Tipo de Dado | Descrição & Escopo | Exemplo / Valor Padrão |
| :--- | :--- | :--- | :--- |
| `listen` | `int` | Porta TCP na qual o servidor Nginx escuta dentro do contêiner. | `8080` |
| `proxy_pass` | `str` | URL de destino interno para onde a requisição é repassada. | `http://gd-backend:8000` |
| `$http_host` | `str` | Variável do Nginx que contém o Host e a Porta originais do cliente.| `137.131.211.210:8080` |
| `client_max_body_size` | `str` | Tamanho máximo permitido para corpo de requisições HTTP (upload).| `100M` |

---

## 5. 🔄 Fluxo de Dados & Contratos de Interface (Public API)

### Trecho de Configuração Relevante (`nginx.conf`):

```nginx
server {
    listen 8080;
    server_name _;

    client_max_body_size 100M;

    location / {
        proxy_pass http://gd-frontend:3000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://gd-backend:8000/;
        proxy_set_header Host $http_host;
    }

    location /qgis {
        proxy_pass http://gd-qgis-server:80/qgis;
        proxy_set_header Host $http_host;
    }
}
```

---

## 6. 🛡️ Matriz de Resiliência, Casos de Borda & Tolerância a Falhas

| Caso de Borda / Falha potencial | Impacto no Sistema | Estratégia de Mitigação / Solução Aplicada |
| :--- | :--- | :--- |
| **Redirecionamento HTTP 307 da API FastAPI removendo a porta 8080** | O cliente é redirecionado para a porta 80 (`ERR_CONNECTION_REFUSED`). | Alteração da diretiva Nginx de `$host` para `$http_host` em todas as rotas `location`. |
| **Upload de arquivo CSV maior do que 1MB** | Erro `413 Request Entity Too Large` retornado pelo Nginx. | Configuração explícita de `client_max_body_size 100M;` na diretiva do servidor. |
| **Contêiner do Backend caindo temporariamente** | Erro `502 Bad Gateway` retornado ao cliente. | Página de erro customizada e política de restart automático nos serviços backend. |

---

## 7. 🧪 Estratégia de Testabilidade & Cobertura (QA)

* **Testes de Roteamento de Redes:** Executados via cURL e inspeção de cabeçalhos HTTP (`curl -I`).
* **Cenários Cobertos:**
  1. Teste de acesso às rotas `/`, `/api/healthcheck` e `/qgis` através do IP público na porta 8080.
  2. Validação da correta passagem de cabeçalhos `X-Forwarded-For` e `Host`.
  3. Verificação do comportamento sob simulação de upload de arquivos grandes.

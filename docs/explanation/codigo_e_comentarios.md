# 💡 Guia de Engenharia: Comentários no Código & Relação com a Documentação

Este documento estabelece as diretrizes formais de **Engenharia de Documentação (Docs-as-Code)** adotadas no projeto **Gêmeo Digital IoT**, esclarecendo como os desenvolvedores devem lidar com comentários no código e como esses comentários se conectam com a documentação do sistema.

---

## 🎯 1. Filosofia de Comentários no Código (Princípios Clean Code)

Na engenharia de software de alta performance, o código-fonte e os comentários possuem responsabilidades estritamente separadas:

### A. A Regra do "PORQUÊ" em vez do "O QUÊ" (Why over What)
* **O "O QUÊ" e o "COMO" pertencem ao próprio código:** Nomes expressivos de variáveis, funções coesas e pequenas, aliados a tipos estáticos (ex: Python type hints, TypeScript), tornam o fluxo autoexplicativo.
* **O "PORQUÊ" pertence ao comentário:** O comentário deve existir exclusivamente para registrar decisões de design não óbvias, justificativas de negócios, limitações de hardware, ressalvas de concorrência ou *workarounds* para bugs de bibliotecas de terceiros.

#### Exemplo de Mau Comentário (Ruído Redundante):
```python
# MÁ PRÁTICA: O comentário apenas repete o que o código faz
i = i + 1  # Incrementa o contador i
```

#### Exemplo de Excelente Comentário (Justificativa de Engenharia):
```python
# BOA PRÁTICA: Explica a razão técnica não óbvia de uma configuração
# O busy_timeout de 5000ms é vital para evitar 'database is locked' no SQLite
# quando o QGIS Server lê o GeoPackage simultaneamente com a escrita da API REST.
cursor.execute("PRAGMA busy_timeout = 5000;")
```

---

## 📜 2. Docstrings como Contratos de Interface (Google Style)

Para todas as funções, métodos e rotas públicas do backend Python (FastAPI / `dyntable`), é obrigatório o uso de **Docstrings** estruturadas.

### Modelo Padrão Adotado:
```python
def registrar_leitura_sensor(sensor_id: str, latitude: float, longitude: float, dados: dict) -> bool:
    """Registra uma nova leitura de telemetria IoT na matriz dinâmica .dyndb.

    Valida os limites geográficos de latitude e longitude referentes à região do
    Pelourinho (Salvador/BA) antes de persistir no banco de dados.

    Args:
        sensor_id (str): Identificador único do dispositivo sensor (ex: 'TEMP_PELO_01').
        latitude (float): Latitude WGS84 em graus decimais (ex: -12.9714).
        longitude (float): Longitude WGS84 em graus decimais (ex: -38.5123).
        dados (dict): Dicionário contendo os pares chave-valor das variáveis IoT.

    Returns:
        bool: True se a gravação e sincronização espacial obtiverem sucesso.

    Raises:
        ValueError: Se a latitude ou longitude estiverem fora dos limites da Bahia.
        DatabaseLockError: Se o banco SQLite exceder o tempo limite no modo WAL.
    """
```

---

## 🔗 3. Como o Código se Relaciona com a Documentação Geral (Single Source of Truth)

A documentação do projeto opera em uma **Hierarquia de Três Camadas (Pai-Filho)**:

```
┌────────────────────────────────────────────────────────────────────────┐
│ CAMADA 1: DOCUMENTAÇÃO DE SISTEMA E ARQUITETURA (Markdown / Diátaxis)  │
│ Arquivos em /docs: Visão C4, Guias How-To, Conceitos e ADRs             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Referencia APIs & Módulos
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ CAMADA 2: DOCUMENTAÇÃO DE API GERADA (OpenAPI / Swagger / Swagger UI) │
│ Gerada AUTOMATICAMENTE pelo FastAPI extraindo Docstrings e Pydantic   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Extraído de
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ CAMADA 3: COMENTÁRIOS DE CÓDIGO & DOCSTRINGS (In-Code Python / JS)      │
│ Contratos de funções, parâmetros, tipos, exceções e o "Why" local       │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Camada 3 -> Camada 2 (Automação de API):** Os desenvolvedores não escrevem nem atualizam tabelas de endpoints HTTP manualmente em arquivos Markdown. Ao atualizar a docstring ou o modelo Pydantic no código Python, o FastAPI gera e atualiza a documentação OpenAPI (`http://localhost:8080/docs`) de forma instantânea.
2. **Camada 1 (Manuais e Arquitetura sob Diátaxis):** Os arquivos `.md` na pasta `/docs` são reservados para visões de alto nível (Diagramas C4, tutoriais de onboarding, guias de deploy na Oracle Cloud OCI e registros formais de decisões de arquitetura - ADRs).

---

## ⛔ 4. Checklist Anti-Patterns de Comentários

 Ao enviar um *Pull Request* ou fazer um *Commit*, certifique-se de:
- [x] **Não manter código comentado:** Apague trechos de código antigos (o histórico do Git serve para consultar versões anteriores).
- [x] **Manter comentários atualizados:** Se alterar a lógica de uma função, atualize a docstring no mesmo *commit*.
- [x] **Evitar comentários óbvios:** Remova comentários que apenas traduzem palavras-chave da linguagem (ex: `# abre o arquivo`, `# fecha a conexão`).
- [x] **Usar tags padronizadas:**
  - `# TODO: [Descrição]` para melhorias planejadas.
  - `# FIXME: [Descrição]` para correções conhecidas temporárias.

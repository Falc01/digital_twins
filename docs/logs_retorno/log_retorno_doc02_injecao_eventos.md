# 📋 Log de Retorno Técnico — Módulo 02: Injeção de Eventos & Padrões Culturais
## Análise de Integração e Ajustes Necessários para Simulação Dinâmica

**Documento Referenciado:** [`docs/explanation/dados_sinteticos/02_injecao_eventos.md`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/docs/explanation/dados_sinteticos/02_injecao_eventos.md)  
**Arquivo de Implementação:** [`backend/src/simulation/events_injection.py`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/backend/src/simulation/events_injection.py)  
**Destinatário:** João Guilherme (Responsável pelo Módulo 02)  
**Status Atual:** Excelente implementação, modular, com 14 testes unitários verdes.

---

### 📌 Contexto da Revisão
O módulo entregue no commit `a163b6c9` está muito bem estruturado: seguiu a arquitetura do projeto, implementou o decaimento gaussiano suave sem condicionais rígidas, colocou a trava de capacidade física nos sensores e integrou os schemas Pydantic de forma limpa.

Durante a auditoria de integração contínua com os módulos de Macro-Fluxo (Doc 01), Circulação de Markov (Doc 03) e Ruído/Saturação (Doc 04), identificamos três pontos técnicos que precisam de refinamento para garantir total estabilidade na execução do gêmeo digital.

---

### Item 1: Sobrescrita Involuntária do Calendário Cultural Fixo ao Enviar Eventos Pontuais

#### 📍 Onde está o problema:
No arquivo [`backend/src/simulation/events_injection.py`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/backend/src/simulation/events_injection.py), dentro do método `evaluate` da classe `EventsInjectionSimulator`:
```python
if self.config.enable_mode1:
    calendar_sources = (
        [e for e in events_registry if e.is_recurring or e.day_of_week is not None]
        if events_registry is not None
        else self._calendar_rules
    )
```

#### ⚠️ Problema (Causa - Consequências):
- **Causa:** O operador ternário substitui integralmente a lista interna de regras do calendário fixo (`self._calendar_rules`, carregada de `calendario_cultural.json`) sempre que o parâmetro `events_registry` for fornecido. Caso uma chamada de API via `POST /api/v1/simulation/events/calculate` envie uma lista contendo apenas um evento de agenda pontual (que não possui dia da semana fixo nem marcação de recorrência), o filtro resulta em uma lista vazia (`[]`).
- **Consequências:** As celebrações culturais tradicionais do bairro (como a Terça da Bênção do Olodum ou a Missa Dominical no Rosário dos Pretos) são completamente anuladas da simulação sempre que um show avulso for consultado ou agendado pelo operador, causando apagões repentinos em eventos históricos consolidados.

#### ✅ Solução (Como e Efeitos):
- **Como:** Modificar a lógica para que as regras de calendário vindas na requisição sejam mescladas/concatenadas à lista base de regras já carregadas do arquivo JSON, substituindo o calendário padrão apenas se o cliente enviar uma flag explícita de anulação intencional.
- **Efeitos:** O sistema passa a manter ativas as tradições semanais do Pelourinho ao mesmo tempo em que processa atrações extras cadastradas pelo operador, sem que um tipo de evento elimine o outro.

---

### Item 2: Efemeridade e Descontinuidade Temporal no Sorteio de Atrações Espontâneas (Modo 3 - Monte Carlo)

#### 📍 Onde está o problema:
No arquivo [`backend/src/simulation/events_injection.py`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/backend/src/simulation/events_injection.py), no bloco do Modo 3 do método `evaluate`:
```python
if u <= self.config.monte_carlo_prob:
    target_j = int(rng.integers(0, J))
    raw_A = float(rng.normal(35.0, 10.0))
    duration = float(rng.uniform(0.5, 1.2))
    ...
    pulse = calculate_gaussian_pulse(
        current_time_hours=t_hours,
        peak_hour=t_hours,  # pico instantâneo da atração de rua
        duration_hours=duration,
        magnitude=calibrated_A,
    )
```

#### ⚠️ Problema (Causa - Consequências):
- **Causa:** O horário de pico da atração sorteada é cravado exatamente na mesma hora da avaliação (`peak_hour = t_hours`) e o simulador não armazena o evento sorteado em memória para os ciclos seguintes.
- **Consequências:** A atração surge instantaneamente em sua amplitude máxima em um ciclo (ex.: às 15h00) e desaparece de forma abrupta logo no ciclo seguinte (às 15h05), ignorando a curva gaussiana de subida e dispersão gradual ($\sigma \approx 1\text{h}$). Além disso, se o simulador avançar minuto a minuto, a cada chamada há 15% de chance de gerar um novo pico imediato, gerando um ruído artificial em dente de serra nas leituras dos sensores.

#### ✅ Solução (Como e Efeitos):
- **Como:** Criar uma lista interna de estado na classe do simulador para armazenar as manifestações espontâneas sorteadas (guardando horário sorteado, nó alvo, duração e amplitude). A cada ciclo de simulação, o módulo avalia a curva contínua de todos os eventos espontâneos ativos e remove da lista apenas aqueles cuja janela temporal de dispersão já tiver se encerrado completamente ($|t - \tau| > 3\sigma$).
- **Efeitos:** As manifestações culturais de rua ganham ciclo de vida orgânico: o público se aglomera aos poucos, atinge o ápice e se dispersa suavemente ao longo de 1 a 2 horas, produzindo telemetria contínua e realista para o gêmeo digital.

---

### Item 3: Dependência Exclusiva do Índice Numérico do Sensor (`sensor_index`)

#### 📍 Onde está o problema:
No arquivo [`backend/src/simulation/events_injection.py`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/backend/src/simulation/events_injection.py):
```python
j = rule.sensor_index
if 0 <= j < J:
```
Em contraste com os arquivos [`backend/shared/calendario_cultural.json`](file:///c:/Users/joaof/Documents/Unifacs/ICs/digital_twins/backend/shared/calendario_cultural.json) e GeoPackage:
```json
"sensor_alvo": "sensor_largo_pelourinho"
```

#### ⚠️ Problema (Causa - Consequências):
- **Causa:** O cálculo do pulso depende estritamente do índice posicional do nó na matriz (`sensor_index`), mas arquivos de configuração e integrações com o banco espacial utilizam o identificador textual do sensor (`sensor_id` ou `sensor_alvo`).
- **Consequências:** Caso um evento seja cadastrado via JSON ou formulário web informando apenas o nome do logradouro (sem saber de antemão a ordem das linhas no banco), o evento corre o risco de cair no sensor de índice 0 (Elevador Lacerda) ou ser descartado por índice inválido.

#### ✅ Solução (Como e Efeitos):
- **Como:** Implementar na inicialização ou no método de avaliação um mecanismo de mapeamento que relacione o identificador textual ao índice numérico correspondente da malha de sensores caso o índice venha ausente ou nulo.
- **Efeitos:** Dá flexibilidade total para que o frontend e os arquivos de configuração cadastrem eventos usando nomes amigáveis de locais (ex.: `"sensor_largo_pelourinho"` ou `"sensor_igreja_rosario"`), garantindo que o público seja injetado no lugar geográfico correto sem erros de alocação.

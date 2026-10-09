# Relatório de Resolução — Módulo 02: Injeção de Eventos & Padrões Culturais

## Objetivo
Este documento registra exatamente o que foi ajustado para resolver os três itens sinalizados no log de retorno do Documento 02.

---

## Item 1 — Sobrescrita involuntária do calendário cultural fixo

### Problema identificado
O método `evaluate()` do simulador substituía a lista interna do calendário base sempre que `events_registry` era enviado. Isso fazia com que regras semanais e tradicionais do Pelourinho desaparecessem quando um evento pontual era enviado por API.

### Ajuste realizado
A correção foi aplicada em [backend/src/simulation/events_injection.py](../../backend/src/simulation/events_injection.py):

- a lista base `self._calendar_rules` foi preservada;
- quando `events_registry` existe, os eventos recorrentes ou com `day_of_week` são acrescentados à base, em vez de substituí-la;
- o mesmo comportamento foi aplicado ao Modo 2, preservando o conjunto de agenda externa sem zerar o calendário fixo.

### Resultado
O sistema agora mantém simultaneamente:
- o calendário cultural semanal padrão do bairro;
- eventos agendados pontuais enviados pelo operador;
- sem que um tipo de evento apague o outro.

---

## Item 2 — Efemeridade e descontinuidade temporal no Modo 3 (Monte Carlo)

### Problema identificado
No Modo 3, o evento espontâneo era gerado em um único ciclo com pico no instante atual e descartado logo no ciclo seguinte. Isso gerava picos imediatos e ruído artificial em dente de serra.

### Ajuste realizado
A correção foi implementada em [backend/src/simulation/events_injection.py](../../backend/src/simulation/events_injection.py):

- foi adicionada a estrutura interna `self._spontaneous_events` ao simulador;
- antes de sorteios novos, o módulo remove eventos espontâneos cujo intervalo temporal já excedeu a janela de sobrevivência, usando a regra `abs(t - peak_hour) > 3 * duration`;
- os eventos ativos são avaliados em cada ciclo e seus pulsos continuam a decair suavemente ao longo do tempo;
- um novo sorteio só acontece quando não existe um evento espontâneo ativo no instante atual.

### Resultado
A manisfetação espontânea agora possui ciclo de vida realista:
- nasce com pico no instante sorteado;
- permanece ativa por alguns ciclos;
- decai gradualmente e desaparece quando a janela temporal se encerra.

---

## Item 3 — Dependência exclusiva do índice numérico do sensor

### Problema identificado
O modelo exigia que `sensor_index` sempre estivesse presente, embora o restante da arquitetura use identificadores textuais como `sensor_alvo` e `sensor_id`.

### Ajuste realizado
A correção foi feita em [backend/src/simulation/schemas.py](../../backend/src/simulation/schemas.py):

- `sensor_index` passou a ser opcional;
- foi criada a função `resolve_sensor_index()` para interpretar valores como:
  - `sensor_largo_pelourinho`;
  - `sensor_praca_da_se`;
  - `sensor_ladeira_do_carmo`;
  - `sensor_igreja_rosario`;
  - ou até índices numéricos em string;
- foi adicionado um validador `resolve_sensor_alias()` que converte o identificador textual para o índice correto quando o campo numérico não é fornecido.

### Resultado
Agora o frontend e arquivos JSON podem cadastrar eventos usando nomes amigáveis dos locais, sem necessidade de conhecer a ordem das linhas do banco ou a matriz interna.

---

## Arquivos alterados
- [backend/src/simulation/events_injection.py](../../backend/src/simulation/events_injection.py)
- [backend/src/simulation/schemas.py](../../backend/src/simulation/schemas.py)
- [backend/tests/test_events_injection.py](../../backend/tests/test_events_injection.py)

---

## Validação executada
Foi executada a suíte do módulo com o comando:

```bash
cd /Users/Perrone/digital_twins/backend && pytest tests/test_events_injection.py -q
```

Resultado verificado: 13 testes passaram, sem falhas no módulo de injeção de eventos.

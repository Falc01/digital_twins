# DIGITAL TWINS IOT — REPOSITORY GOVERNANCE & ARCHITECTURE (ATLAS v2.4)

```yaml
version: "2.4"
project: "digital_twins"
domain: "Urban IoT Digital Twin — Pedestrian Sensing & Synthetic Traffic Simulation"
institution: "UNIFACS — Iniciação Científica (IC)"
blast_radius: "C:/Users/joaof/Documents/Unifacs/ICs/digital_twins/"
owner: "João Spinola Falcão"

tech_stack:
  backend: "FastAPI, Python 3.12+, Uvicorn, Pydantic v2"
  spatial_data: "GeoPackage SQLite (.gpkg), Shapely, GeoPandas"
  gis_rendering: "QGIS Server Headless (WMS/WFS)"
  frontend: "Leaflet.js, Node.js, HTML5/CSS3"
  infra: "Docker Compose (5 containers), Nginx Gateway (port 8080)"
  simulation_suite: "Synthetic Data Framework Docs 00 to 05 (91/91 tests green)"

telemetry:
  footer_style: "v2.3_accumulated_hybrid"
  mandatory_in_substantive_responses: true
  canonical_template: |
    ---
    🪙 **Telemetria de Tokens**:
      • 📥 **Entrada**: ~{X} tokens | 📤 **Saída**: ~{Y} tokens | ⏱️ **Latência**: ~{Z}s  
      • 💵 **Custo Turno**: ~${W} USD | 💰 **Custo Acumulado**: ~${Total} USD  
      • 📈 **Janela Acumulada**: ~{K}k tokens | Persistência: English (Dense YAML)  
    📊 **Janela de Contexto**:  
      • 💬 **Chat Atual**: [Turno {N}] {🟢 Leve (<25k) / 🟡 Atenção (25k-60k) / 🔴 Saturado (>60k)}  
      • 📁 **Projeto (.agents)**: {🟢 Saudável (<15KB) / 🟡 Compactação pendente / 🔴 Memória pesada}
  formatting_rule: "Each line must end with two trailing spaces to prevent soft-break markdown collapse."

context_persistence_protocol:
  session_task_wrapup:
    mandatory: true
    trigger: "Upon completing any simulation change, bugfix, architectural update, or audit cycle."
    action: "Surgically sync .agents/memory/ (activeContext.md, decisionsLog.md, progress.md, auditLog.md) BEFORE final response delivery."
    sliding_window_compliance: "Keep Hot Storage strictly under 15KB-20KB; archive completed/stale entries to archive/."

cadence_circuit_breaker:
  tool_limits:
    exploratory_debug: 8
    feature_scaffolding_execution: 30
  continuous_execution_allowed: true
  anti_blind_trial_and_error:
    consecutive_test_failure_limit: 2
    action: HALT_IMMEDIATELY_AND_TRIGGER_MODEL_ESCALATION
  model_escalation_protocol:
    baseline_model: "Gemini 3.8 Flash (High)"
    frontier_target: "Gemini 4 Argon"
    instant_escalation_domains:
      - "Complex Concurrency & Race Conditions in Multi-Container Docker Sync"
      - "Advanced Spatial Geometry & Topology Network Solvers (Markovian Matrix Inversions)"
      - "Heisenbugs & Asynchronous Event Deadlocks in Sensor Bar"

bilingual_efficiency_protocol:
  interaction_chat: "Português (PT-BR) fluente, direto e parceiro."
  persistence_internal: "Dense Technical English for specs, memory files, and internal configs."
```

## 📁 Modular Simulation Framework (Docs 00-05)
- **Doc 00**: Central Data Bus & Ingestion into GeoPackage.
- **Doc 01**: Circadian Macro-Flow Subsystem ($N_{\text{rotina}}$) — Multi-modal curves.
- **Doc 02**: Dynamic Event & Cultural POI Injection ($E(t)$).
- **Doc 03**: Network Circulation via Markov Chains & Gravity Model ($P_{ij}$).
- **Doc 04**: Richards Saturation, IoT Sensor Noise & Telemetry Data Lake.
- **Doc 05**: Input/Output Contracts & Service Interfaces.

from __future__ import annotations

TYPE_COLORS: dict[str, str] = {
    "FLOAT":     "type-float",
    "INT":       "type-int",
    "STRING":    "type-string",
    "BOOL":      "type-bool",
    "TIMESTAMP": "type-timestamp",
    "AUTO":      "type-auto",
    "NULL":      "type-auto",
}


def type_badge(dtype_name: str) -> str:
    cls = TYPE_COLORS.get(dtype_name, "type-auto")
    return f'<span class="type-tag {cls}">{dtype_name}</span>'

_CSS = """
<style>
  /* ── Fontes ──────────────────────────────────────────────── */
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

  html, body, [class*="css"]      { font-family: 'Syne', sans-serif; }
  code, pre, .stCode,
  .mono                           { font-family: 'JetBrains Mono', monospace !important; }

  /* ── Layout global ──────────────────────────────────────── */
  .block-container                { padding-top: 1.5rem; }
  [data-testid="stSidebar"]       { background: #0a0a0a; border-right: 1px solid #1a1a1a; }

  /* ── Cabeçalho ───────────────────────────────────────────── */
  .main-header {
    background: linear-gradient(135deg, #0f0f0f 0%, #0d1f18 100%);
    border: 1px solid #00ff88;
    border-radius: 8px;
    padding: 1.2rem 1.8rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
  }
  .main-header::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 180px; height: 180px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(0,255,136,0.08) 0%, transparent 70%);
    pointer-events: none;
  }
  .main-header h1 {
    color: #00ff88;
    font-size: 1.8rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.5px;
  }
  .main-header p  { color: #555; margin: 0.2rem 0 0; font-size: 0.82rem; }

  /* ── Métricas ────────────────────────────────────────────── */
  .metric-card {
    background: #0e0e0e;
    border: 1px solid #1e1e1e;
    border-radius: 6px;
    padding: 1rem;
    text-align: center;
    transition: border-color 0.2s;
  }
  .metric-card:hover      { border-color: #2a2a2a; }
  .metric-val             { font-size: 2rem; font-weight: 800; color: #00ff88; line-height: 1; }
  .metric-lbl             { font-size: 0.7rem; color: #444; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 4px; }

  /* ── Badges de tipo ─────────────────────────────────────── */
  .type-tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 0.68rem;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    letter-spacing: 0.5px;
  }
  .type-float     { background: #0d2018; color: #00ff88; border: 1px solid #00ff8844; }
  .type-int       { background: #0d1a28; color: #00aaff; border: 1px solid #00aaff44; }
  .type-string    { background: #281a0d; color: #ffaa00; border: 1px solid #ffaa0044; }
  .type-bool      { background: #280d1a; color: #ff44aa; border: 1px solid #ff44aa44; }
  .type-timestamp { background: #1a0d28; color: #aa44ff; border: 1px solid #aa44ff44; }
  .type-auto      { background: #1a1a1a; color: #555;    border: 1px solid #2a2a2a;   }

  /* ── Tabela de dados ─────────────────────────────────────── */
  .data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
    font-family: 'JetBrains Mono', monospace;
  }
  .data-table th {
    background: #0c0c0c;
    color: #00ff88;
    padding: 9px 14px;
    text-align: left;
    border-bottom: 2px solid #00ff8830;
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    white-space: nowrap;
  }
  .data-table td {
    padding: 7px 14px;
    border-bottom: 1px solid #141414;
    color: #bbb;
    vertical-align: middle;
  }
  .data-table tr:hover td  { background: #0f0f0f; }
  .data-table .null-cell   { color: #2a2a2a; font-style: italic; }
  .data-table .id-cell     { color: #3a3a3a; font-size: 0.75rem; }
  .data-table .bool-true   { color: #00ff88; }
  .data-table .bool-false  { color: #ff4466; }

  /* ── Botões ──────────────────────────────────────────────── */
  .stButton button {
    background: #0e0e0e;
    border: 1px solid #282828;
    color: #aaa;
    border-radius: 4px;
    transition: all 0.15s;
  }
  .stButton button:hover  { border-color: #00ff88; color: #00ff88; }
  .btn-active button      { border-color: #00ff88 !important; color: #00ff88 !important; background: #0a1f0f !important; }
  .qgis-btn button {
    background: #0a1a0d !important;
    border: 1px solid #00aa5566 !important;
    color: #00aa55 !important;
    font-weight: 700 !important;
  }
  .qgis-btn button:hover  { border-color: #00ff88 !important; color: #00ff88 !important; }

  /* ── Notificações / log ──────────────────────────────────── */
  .notif {
    padding: 7px 12px;
    border-radius: 4px;
    font-size: 0.8rem;
    font-family: 'JetBrains Mono', monospace;
    margin: 3px 0;
  }
  .notif-ok  { background: #091508; border-left: 3px solid #00ff88; color: #00cc66; }
  .notif-err { background: #150808; border-left: 3px solid #ff4444; color: #ff6666; }
  .notif-inf { background: #08101a; border-left: 3px solid #0088ff; color: #44aaff; }

  /* ── Títulos de seção (sidebar) ──────────────────────────── */
  .section-title {
    font-size: 0.65rem;
    color: #333;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 1rem 0 0.4rem;
    padding-bottom: 4px;
    border-bottom: 1px solid #1a1a1a;
  }

  /* ── Estado vazio ────────────────────────────────────────── */
  .no-table {
    color: #333;
    text-align: center;
    padding: 4rem 2rem;
    font-size: 1rem;
    line-height: 1.8;
  }
  .no-table .arrow { color: #00ff8840; font-size: 2rem; display: block; margin-bottom: 1rem; }

  /* ── Matrix info box ─────────────────────────────────────── */
  .matrix-info {
    background: #0a0f0d;
    border: 1px solid #0d2018;
    border-radius: 6px;
    padding: 10px 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #2a5a3a;
    margin: 8px 0;
  }
  .matrix-info .hi { color: #00ff88; }
</style>
"""


def get_styles() -> str:
  return _CSS
"""
app.py — Interface web para o DynTable
Execute com: streamlit run app.py
"""

import streamlit as st
import time
import io
from dyntable import DynTable, DynType, DuplicateColumnError, ColumnNotFoundError

# ─────────────────────────────────────────────
#  CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="DynTable IoT",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  ESTILOS CUSTOMIZADOS
# ─────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');

  html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
  code, pre, .stCode { font-family: 'JetBrains Mono', monospace !important; }

  .block-container { padding-top: 1.5rem; }

  /* Cabeçalho principal */
  .main-header {
    background: linear-gradient(135deg, #0f0f0f 0%, #1a1a2e 100%);
    border: 1px solid #00ff88;
    border-radius: 8px;
    padding: 1.2rem 1.8rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  .main-header h1 {
    color: #00ff88;
    font-size: 1.8rem;
    font-weight: 800;
    margin: 0;
    font-family: 'Syne', sans-serif;
    letter-spacing: -0.5px;
  }
  .main-header p { color: #888; margin: 0; font-size: 0.85rem; }

  /* Cards de métricas */
  .metric-card {
    background: #111;
    border: 1px solid #222;
    border-radius: 6px;
    padding: 1rem;
    text-align: center;
  }
  .metric-val { font-size: 2rem; font-weight: 800; color: #00ff88; }
  .metric-lbl { font-size: 0.75rem; color: #666; text-transform: uppercase; letter-spacing: 1px; }

  /* Tags de tipo */
  .type-tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 0.7rem;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    letter-spacing: 0.5px;
  }
  .type-float   { background: #1a3a2a; color: #00ff88; border: 1px solid #00ff88; }
  .type-int     { background: #1a2a3a; color: #00aaff; border: 1px solid #00aaff; }
  .type-string  { background: #3a2a1a; color: #ffaa00; border: 1px solid #ffaa00; }
  .type-bool    { background: #3a1a2a; color: #ff44aa; border: 1px solid #ff44aa; }
  .type-timestamp { background: #2a1a3a; color: #aa44ff; border: 1px solid #aa44ff; }
  .type-auto    { background: #222; color: #666; border: 1px solid #333; }

  /* Tabela de dados */
  .data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    font-family: 'JetBrains Mono', monospace;
  }
  .data-table th {
    background: #0f0f0f;
    color: #00ff88;
    padding: 8px 12px;
    text-align: left;
    border-bottom: 2px solid #00ff88;
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  .data-table td {
    padding: 7px 12px;
    border-bottom: 1px solid #1a1a1a;
    color: #ccc;
    vertical-align: middle;
  }
  .data-table tr:hover td { background: #111; }
  .data-table .null-cell { color: #333; font-style: italic; }
  .data-table .id-cell { color: #555; }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: #0a0a0a;
    border-right: 1px solid #1a1a1a;
  }
  [data-testid="stSidebar"] .stButton button {
    width: 100%;
  }

  /* Botões */
  .stButton button {
    background: #0f0f0f;
    border: 1px solid #333;
    color: #ccc;
    border-radius: 4px;
    transition: all 0.15s;
  }
  .stButton button:hover {
    border-color: #00ff88;
    color: #00ff88;
  }

  /* Notificações */
  .notif {
    padding: 8px 14px;
    border-radius: 4px;
    font-size: 0.85rem;
    margin: 6px 0;
    font-family: 'JetBrains Mono', monospace;
  }
  .notif-ok  { background: #0a1f0f; border-left: 3px solid #00ff88; color: #00ff88; }
  .notif-err { background: #1f0a0a; border-left: 3px solid #ff4444; color: #ff4444; }
  .notif-inf { background: #0a0f1f; border-left: 3px solid #0088ff; color: #0088ff; }

  .section-title {
    font-size: 0.7rem;
    color: #444;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 1rem 0 0.5rem;
    font-family: 'Syne', sans-serif;
  }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  ESTADO DA SESSÃO (persiste entre reruns)
# ─────────────────────────────────────────────
if "table" not in st.session_state:
    st.session_state.table = DynTable("sensor_readings")

if "log" not in st.session_state:
    st.session_state.log = []

def log(msg: str, kind: str = "ok"):
    ts = time.strftime("%H:%M:%S")
    st.session_state.log.insert(0, {"ts": ts, "msg": msg, "kind": kind})
    if len(st.session_state.log) > 50:
        st.session_state.log.pop()

table: DynTable = st.session_state.table

# ─────────────────────────────────────────────
#  HELPERS DE RENDERIZAÇÃO
# ─────────────────────────────────────────────
TYPE_COLORS = {
    "FLOAT": "type-float", "INT": "type-int", "STRING": "type-string",
    "BOOL": "type-bool", "TIMESTAMP": "type-timestamp", "AUTO": "type-auto",
    "NULL": "type-auto", "BYTES": "type-auto",
}

def type_badge(dtype_name: str) -> str:
    cls = TYPE_COLORS.get(dtype_name, "type-auto")
    return f'<span class="type-tag {cls}">{dtype_name}</span>'

# ─────────────────────────────────────────────
#  CABEÇALHO
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="main-header">
  <div>⚡</div>
  <div>
    <h1>DynTable IoT</h1>
    <p>Tabela dinâmica · colunas adicionadas em runtime · sem esquema fixo</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  MÉTRICAS RÁPIDAS
# ─────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{table.row_count}</div><div class="metric-lbl">linhas</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{table.col_count}</div><div class="metric-lbl">colunas</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{table._next_id - 1}</div><div class="metric-lbl">total inserido</div></div>', unsafe_allow_html=True)
with m4:
    null_count = sum(
        1 for row in table
        for col in table.column_names
        if row.cell(col).is_null
    ) if table.col_count > 0 else 0
    st.markdown(f'<div class="metric-card"><div class="metric-val">{null_count}</div><div class="metric-lbl">células null</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  LAYOUT PRINCIPAL
# ─────────────────────────────────────────────
col_table, col_side = st.columns([3, 1])

# ══════════════════════════════════════════════
#  PAINEL ESQUERDO: TABELA DE DADOS
# ══════════════════════════════════════════════
with col_table:

    # ── Abas ──────────────────────────────────
    tab_data, tab_schema, tab_stats, tab_csv = st.tabs(
        ["📋 Dados", "🗂 Schema", "📊 Estatísticas", "📤 Exportar CSV"]
    )

    # ── ABA: DADOS ────────────────────────────
    with tab_data:
        if not table.col_count:
            st.markdown('<div class="notif notif-inf">Nenhuma coluna ainda. Adicione colunas na barra lateral.</div>', unsafe_allow_html=True)
        elif not table.row_count:
            st.markdown('<div class="notif notif-inf">Nenhuma linha ainda. Use o painel lateral para inserir dados.</div>', unsafe_allow_html=True)
        else:
            # Filtro rápido
            filter_col = st.selectbox("Filtrar por coluna:", ["(sem filtro)"] + table.column_names, key="filter_col")
            if filter_col != "(sem filtro)":
                filter_val = st.text_input("Valor do filtro:", key="filter_val")
            else:
                filter_val = ""

            # Renderiza tabela HTML
            headers = "".join(
                f"<th>{n} {type_badge(table._columns[n].dtype.name)}</th>"
                for n in table.column_names
            )
            header_row = f"<tr><th>#ID</th><th>criado_em</th>{headers}</tr>"

            rows_html = ""
            for row in table:
                # Aplica filtro
                if filter_col != "(sem filtro)" and filter_val:
                    cell_val = str(row[filter_col]) if row[filter_col] is not None else ""
                    if filter_val.lower() not in cell_val.lower():
                        continue

                cells = ""
                for col in table.column_names:
                    cell = row.cell(col)
                    if cell.is_null:
                        cells += '<td class="null-cell">NULL</td>'
                    else:
                        cells += f"<td>{cell.formatted()}</td>"

                rows_html += f'<tr><td class="id-cell">{row.id}</td><td class="id-cell">{row.created_at_str}</td>{cells}</tr>'

            st.markdown(
                f'<table class="data-table"><thead>{header_row}</thead><tbody>{rows_html}</tbody></table>',
                unsafe_allow_html=True
            )

            # Deletar linha
            st.markdown('<p class="section-title">⚠ Remover linha</p>', unsafe_allow_html=True)
            del_id = st.number_input("ID da linha para deletar:", min_value=1, step=1, key="del_row_id")
            if st.button("🗑 Deletar linha", key="btn_del_row"):
                try:
                    table.delete_row(int(del_id))
                    log(f"Linha {del_id} removida.", "ok")
                    st.rerun()
                except Exception as e:
                    log(str(e), "err")
                    st.rerun()

    # ── ABA: SCHEMA ───────────────────────────
    with tab_schema:
        if not table.col_count:
            st.markdown('<div class="notif notif-inf">Nenhuma coluna definida ainda.</div>', unsafe_allow_html=True)
        else:
            schema_html = """
            <table class="data-table">
              <thead><tr><th>Nome</th><th>Tipo</th><th>Nullable</th><th>Travado</th></tr></thead>
              <tbody>
            """
            for col in table.columns:
                nullable  = "✓" if col.nullable else "✗"
                locked    = "🔒" if col.locked else "—"
                schema_html += f"<tr><td>{col.name}</td><td>{type_badge(col.dtype.name)}</td><td>{nullable}</td><td>{locked}</td></tr>"
            schema_html += "</tbody></table>"
            st.markdown(schema_html, unsafe_allow_html=True)

            # Renomear coluna
            st.markdown('<p class="section-title">Renomear coluna</p>', unsafe_allow_html=True)
            r1c, r2c = st.columns(2)
            with r1c:
                old_name = st.selectbox("Coluna:", table.column_names, key="rename_old")
            with r2c:
                new_name = st.text_input("Novo nome:", key="rename_new")
            if st.button("↩ Renomear", key="btn_rename"):
                try:
                    table.rename_column(old_name, new_name.strip())
                    log(f"'{old_name}' renomeada para '{new_name}'.", "ok")
                    st.rerun()
                except Exception as e:
                    log(str(e), "err")
                    st.rerun()

            # Remover coluna
            st.markdown('<p class="section-title">⚠ Remover coluna</p>', unsafe_allow_html=True)
            rm_col = st.selectbox("Coluna para remover:", table.column_names, key="rm_col")
            if st.button("🗑 Remover coluna", key="btn_rm_col"):
                try:
                    table.remove_column(rm_col)
                    log(f"Coluna '{rm_col}' removida.", "ok")
                    st.rerun()
                except Exception as e:
                    log(str(e), "err")
                    st.rerun()

    # ── ABA: ESTATÍSTICAS ─────────────────────
    with tab_stats:
        if not table.col_count or not table.row_count:
            st.markdown('<div class="notif notif-inf">Sem dados suficientes para estatísticas.</div>', unsafe_allow_html=True)
        else:
            numeric_cols = [
                n for n, col in table._columns.items()
                if col.dtype in (DynType.INT, DynType.FLOAT, DynType.AUTO)
            ]
            if not numeric_cols:
                st.markdown('<div class="notif notif-inf">Nenhuma coluna numérica encontrada.</div>', unsafe_allow_html=True)
            else:
                stats_html = """
                <table class="data-table">
                  <thead><tr><th>Coluna</th><th>Count</th><th>Nulls</th><th>Min</th><th>Max</th><th>Média</th></tr></thead>
                  <tbody>
                """
                for col_name in numeric_cols:
                    s = table.column_stats(col_name)
                    avg = f"{s['avg']:.3f}" if s['avg'] is not None else "—"
                    mn  = f"{s['min']}"     if s['min'] is not None else "—"
                    mx  = f"{s['max']}"     if s['max'] is not None else "—"
                    stats_html += f"<tr><td>{col_name}</td><td>{s['count']}</td><td>{s['nulls']}</td><td>{mn}</td><td>{mx}</td><td>{avg}</td></tr>"
                stats_html += "</tbody></table>"
                st.markdown(stats_html, unsafe_allow_html=True)

    # ── ABA: EXPORTAR CSV ─────────────────────
    with tab_csv:
        if table.row_count == 0:
            st.markdown('<div class="notif notif-inf">Nenhuma linha para exportar.</div>', unsafe_allow_html=True)
        else:
            csv_str = table.to_csv_string()
            st.download_button(
                label="⬇ Baixar CSV",
                data=csv_str.encode("utf-8"),
                file_name=f"{table.name}.csv",
                mime="text/csv",
            )
            st.markdown('<p class="section-title">Pré-visualização</p>', unsafe_allow_html=True)
            st.code(csv_str[:2000] + ("..." if len(csv_str) > 2000 else ""), language="text")

# ══════════════════════════════════════════════
#  BARRA LATERAL: CONTROLES
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown(f'<p style="color:#00ff88; font-size:1.1rem; font-weight:800; font-family:Syne,sans-serif;">⚡ {table.name}</p>', unsafe_allow_html=True)

    # ── Renomear tabela ───────────────────────
    with st.expander("📝 Renomear tabela"):
        new_table_name = st.text_input("Novo nome:", value=table.name, key="new_table_name")
        if st.button("Salvar nome"):
            try:
                table.name = new_table_name.strip()
                log(f"Tabela renomeada para '{table.name}'.", "ok")
                st.rerun()
            except Exception as e:
                log(str(e), "err")
                st.rerun()

    st.divider()

    # ── ADICIONAR COLUNA ──────────────────────
    st.markdown('<p class="section-title">Nova coluna</p>', unsafe_allow_html=True)

    new_col_name = st.text_input("Nome da coluna:", key="new_col_name", placeholder="ex: temperatura_c")

    type_options = ["AUTO (inferido)", "FLOAT", "INT", "STRING", "BOOL", "TIMESTAMP"]
    type_map = {
        "AUTO (inferido)": DynType.AUTO,
        "FLOAT":     DynType.FLOAT,
        "INT":       DynType.INT,
        "STRING":    DynType.STRING,
        "BOOL":      DynType.BOOL,
        "TIMESTAMP": DynType.TIMESTAMP,
    }
    new_col_type   = st.selectbox("Tipo:", type_options, key="new_col_type")
    new_col_nullable = st.checkbox("Nullable (aceita NULL)", value=True, key="new_col_nullable")

    if st.button("➕ Adicionar coluna", key="btn_add_col"):
        name = new_col_name.strip()
        if not name:
            log("Nome da coluna não pode ser vazio.", "err")
        else:
            try:
                table.add_column(name, type_map[new_col_type], new_col_nullable)
                log(f"Coluna '{name}' ({new_col_type}) adicionada.", "ok")
                st.rerun()
            except Exception as e:
                log(str(e), "err")
                st.rerun()

    st.divider()

    # ── INSERIR LINHA ─────────────────────────
    st.markdown('<p class="section-title">Nova linha</p>', unsafe_allow_html=True)

    if not table.col_count:
        st.markdown('<div class="notif notif-inf" style="font-size:0.75rem">Adicione colunas primeiro.</div>', unsafe_allow_html=True)
    else:
        row_values = {}
        for col in table.columns:
            dtype = col.dtype

            if dtype in (DynType.FLOAT, DynType.AUTO):
                v = st.text_input(f"{col.name}:", key=f"ri_{col.name}", placeholder="ex: 23.7 (ou vazio para NULL)")
                if v.strip():
                    try:    row_values[col.name] = float(v)
                    except: row_values[col.name] = v

            elif dtype == DynType.INT:
                v = st.text_input(f"{col.name}:", key=f"ri_{col.name}", placeholder="ex: 42 (ou vazio para NULL)")
                if v.strip():
                    try:    row_values[col.name] = int(v)
                    except: row_values[col.name] = v

            elif dtype == DynType.BOOL:
                v = st.selectbox(f"{col.name}:", ["NULL", "true", "false"], key=f"ri_{col.name}")
                if v != "NULL":
                    row_values[col.name] = (v == "true")

            elif dtype == DynType.TIMESTAMP:
                v = st.checkbox(f"{col.name} = agora?", key=f"ri_{col.name}")
                if v:
                    row_values[col.name] = time.time()

            else:  # STRING
                v = st.text_input(f"{col.name}:", key=f"ri_{col.name}", placeholder="ex: sensor-01")
                if v.strip():
                    row_values[col.name] = v

        if st.button("🚀 Inserir linha", key="btn_insert_row"):
            try:
                row = table.new_row(**row_values)
                log(f"Linha {row.id} inserida com {len(row_values)} campo(s).", "ok")
                st.rerun()
            except Exception as e:
                log(str(e), "err")
                st.rerun()

    st.divider()

    # ── RESET ─────────────────────────────────
    if st.button("🔄 Nova tabela (reset)", key="btn_reset"):
        st.session_state.table = DynTable("sensor_readings")
        st.session_state.log = []
        log("Tabela reiniciada.", "inf")
        st.rerun()

    st.divider()

    # ── LOG DE ATIVIDADE ──────────────────────
    st.markdown('<p class="section-title">Log de atividade</p>', unsafe_allow_html=True)
    for entry in st.session_state.log[:12]:
        st.markdown(
            f'<div class="notif notif-{entry["kind"]}" style="margin:3px 0;font-size:0.72rem;">'
            f'<span style="opacity:0.5">{entry["ts"]}</span>  {entry["msg"]}</div>',
            unsafe_allow_html=True
        )

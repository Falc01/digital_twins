"""
app_v2.py — Interface Streamlit para o DynTable
================================================
Este arquivo é APENAS a camada visual.

Toda lógica de negócio vive em:
  config.py         → configurações (pasta, defaults)
  table_manager.py  → criar, listar, deletar, salvar tabelas
  dyntable/         → operações dentro de cada tabela

Se você quiser trocar o Streamlit por outro framework,
você mantém config.py e table_manager.py intocados
e só reescreve este arquivo.

Execute com:
    streamlit run app_v2.py
"""

import streamlit as st
import time
from dyntable import DynTable, DynType, DuplicateColumnError
from table_manager import TableManager, TableNotFoundError, TableAlreadyExistsError
from config import PASTA_DADOS, TABELA_PADRAO

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
#  ESTILOS
# ─────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap');
  html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
  code, pre, .stCode { font-family: 'JetBrains Mono', monospace !important; }
  .block-container { padding-top: 1.5rem; }
  .main-header {
    background: linear-gradient(135deg, #0f0f0f 0%, #1a1a2e 100%);
    border: 1px solid #00ff88; border-radius: 8px;
    padding: 1.2rem 1.8rem; margin-bottom: 1.5rem;
  }
  .main-header h1 { color: #00ff88; font-size: 1.8rem; font-weight: 800; margin: 0; letter-spacing: -0.5px; }
  .main-header p  { color: #888; margin: 0; font-size: 0.85rem; }
  .metric-card { background: #111; border: 1px solid #222; border-radius: 6px; padding: 1rem; text-align: center; }
  .metric-val  { font-size: 2rem; font-weight: 800; color: #00ff88; }
  .metric-lbl  { font-size: 0.75rem; color: #666; text-transform: uppercase; letter-spacing: 1px; }
  .type-tag    { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 0.7rem;
                 font-family: 'JetBrains Mono', monospace; font-weight: 700; letter-spacing: 0.5px; }
  .type-float  { background:#1a3a2a; color:#00ff88; border:1px solid #00ff88; }
  .type-int    { background:#1a2a3a; color:#00aaff; border:1px solid #00aaff; }
  .type-string { background:#3a2a1a; color:#ffaa00; border:1px solid #ffaa00; }
  .type-bool   { background:#3a1a2a; color:#ff44aa; border:1px solid #ff44aa; }
  .type-timestamp { background:#2a1a3a; color:#aa44ff; border:1px solid #aa44ff; }
  .type-auto   { background:#222; color:#666; border:1px solid #333; }
  .data-table  { width:100%; border-collapse:collapse; font-size:0.85rem; font-family:'JetBrains Mono',monospace; }
  .data-table th { background:#0f0f0f; color:#00ff88; padding:8px 12px; text-align:left;
                   border-bottom:2px solid #00ff88; font-family:'Syne',sans-serif;
                   font-weight:700; font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; }
  .data-table td { padding:7px 12px; border-bottom:1px solid #1a1a1a; color:#ccc; vertical-align:middle; }
  .data-table tr:hover td { background:#111; }
  .data-table .null-cell { color:#333; font-style:italic; }
  .data-table .id-cell   { color:#555; }
  .table-card { background:#111; border:1px solid #222; border-radius:6px; padding:12px 16px;
                margin:4px 0; cursor:pointer; transition:border-color 0.15s; }
  .table-card:hover { border-color:#00ff88; }
  .table-card.active { border-color:#00ff88; background:#0a1f0f; }
  .table-card .tc-name { color:#00ff88; font-weight:700; font-size:0.95rem; }
  .table-card .tc-meta { color:#555; font-size:0.75rem; font-family:'JetBrains Mono',monospace; }
  [data-testid="stSidebar"] { background:#0a0a0a; border-right:1px solid #1a1a1a; }
  .stButton button { background:#0f0f0f; border:1px solid #333; color:#ccc;
                     border-radius:4px; transition:all 0.15s; }
  .stButton button:hover { border-color:#00ff88; color:#00ff88; }
  .notif { padding:8px 14px; border-radius:4px; font-size:0.85rem; margin:4px 0;
           font-family:'JetBrains Mono',monospace; }
  .notif-ok  { background:#0a1f0f; border-left:3px solid #00ff88; color:#00ff88; }
  .notif-err { background:#1f0a0a; border-left:3px solid #ff4444; color:#ff4444; }
  .notif-inf { background:#0a0f1f; border-left:3px solid #0088ff; color:#0088ff; }
  .section-title { font-size:0.7rem; color:#444; text-transform:uppercase;
                   letter-spacing:2px; margin:1rem 0 0.5rem; }
  .no-table { color:#444; text-align:center; padding:3rem; font-size:0.95rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  ESTADO DA SESSÃO
# ─────────────────────────────────────────────
if "mgr" not in st.session_state:
    # TableManager lê a pasta — descobre tabelas existentes automaticamente
    st.session_state.mgr = TableManager(PASTA_DADOS)

if "active_table" not in st.session_state:
    # Tenta abrir a tabela padrão definida em config.py
    mgr: TableManager = st.session_state.mgr
    if TABELA_PADRAO and mgr.exists(TABELA_PADRAO):
        st.session_state.active_table = mgr.get(TABELA_PADRAO)
    elif mgr.list_tables():
        # Se não tem padrão, abre a primeira disponível
        st.session_state.active_table = mgr.get(mgr.list_tables()[0])
    else:
        st.session_state.active_table = None

if "log" not in st.session_state:
    st.session_state.log = []

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
mgr: TableManager = st.session_state.mgr

def get_table() -> DynTable | None:
    return st.session_state.active_table

def set_table(t: DynTable | None):
    st.session_state.active_table = t

def autosave():
    t = get_table()
    if t:
        mgr.save(t)

def log(msg: str, kind: str = "ok"):
    ts = time.strftime("%H:%M:%S")
    st.session_state.log.insert(0, {"ts": ts, "msg": msg, "kind": kind})
    if len(st.session_state.log) > 50:
        st.session_state.log.pop()

TYPE_COLORS = {
    "FLOAT":"type-float","INT":"type-int","STRING":"type-string",
    "BOOL":"type-bool","TIMESTAMP":"type-timestamp","AUTO":"type-auto","NULL":"type-auto",
}
def type_badge(dtype_name: str) -> str:
    cls = TYPE_COLORS.get(dtype_name, "type-auto")
    return f'<span class="type-tag {cls}">{dtype_name}</span>'

# ─────────────────────────────────────────────
#  CABEÇALHO
# ─────────────────────────────────────────────
table = get_table()
table_label = f"· {table.name}" if table else "· nenhuma tabela selecionada"
st.markdown(f"""
<div class="main-header">
  <h1>⚡ DynTable IoT <span style="font-weight:400;color:#444;font-size:1.1rem">{table_label}</span></h1>
  <p>Tabela dinâmica · colunas em runtime · múltiplas tabelas · sem esquema fixo</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  MÉTRICAS
# ─────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
all_tables = mgr.list_tables()
with m1:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{len(all_tables)}</div><div class="metric-lbl">tabelas</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{table.row_count if table else "—"}</div><div class="metric-lbl">linhas</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{table.col_count if table else "—"}</div><div class="metric-lbl">colunas</div></div>', unsafe_allow_html=True)
with m4:
    null_count = sum(1 for row in table for col in table.column_names if row.cell(col).is_null) if table and table.col_count else 0
    st.markdown(f'<div class="metric-card"><div class="metric-val">{null_count if table else "—"}</div><div class="metric-lbl">células null</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
#  LAYOUT PRINCIPAL
# ═══════════════════════════════════════════════════════════
col_main, col_side = st.columns([3, 1])

# ── PAINEL PRINCIPAL ──────────────────────────────────────
with col_main:

    if not table:
        st.markdown('<div class="no-table">Nenhuma tabela selecionada.<br>Crie uma nova na barra lateral →</div>', unsafe_allow_html=True)
    else:
        tab_data, tab_schema, tab_stats, tab_csv = st.tabs(
            ["📋 Dados", "🗂 Schema", "📊 Estatísticas", "📤 Exportar CSV"]
        )

        # ── ABA DADOS ──────────────────────────────────────
        with tab_data:
            if not table.col_count:
                st.markdown('<div class="notif notif-inf">Nenhuma coluna ainda. Adicione na barra lateral.</div>', unsafe_allow_html=True)
            elif not table.row_count:
                st.markdown('<div class="notif notif-inf">Nenhuma linha ainda. Use o painel lateral para inserir dados.</div>', unsafe_allow_html=True)
            else:
                filter_col = st.selectbox("Filtrar por coluna:", ["(sem filtro)"] + table.column_names, key="filter_col")
                filter_val = st.text_input("Valor:", key="filter_val") if filter_col != "(sem filtro)" else ""

                headers = "".join(f"<th>{n} {type_badge(table._columns[n].dtype.name)}</th>" for n in table.column_names)
                rows_html = ""
                for row in table:
                    if filter_col != "(sem filtro)" and filter_val:
                        cell_val = str(row[filter_col]) if row[filter_col] is not None else ""
                        if filter_val.lower() not in cell_val.lower():
                            continue
                    cells = "".join(
                        f'<td class="null-cell">NULL</td>' if row.cell(col).is_null
                        else f"<td>{row.cell(col).formatted()}</td>"
                        for col in table.column_names
                    )
                    rows_html += f'<tr><td class="id-cell">{row.id}</td><td class="id-cell">{row.created_at_str}</td>{cells}</tr>'

                st.markdown(
                    f'<table class="data-table"><thead><tr><th>#ID</th><th>criado_em</th>{headers}</tr></thead><tbody>{rows_html}</tbody></table>',
                    unsafe_allow_html=True
                )

                st.markdown('<p class="section-title">⚠ Remover linha</p>', unsafe_allow_html=True)
                del_id = st.number_input("ID:", min_value=1, step=1, key="del_row_id")
                if st.button("🗑 Deletar linha"):
                    try:
                        table.delete_row(int(del_id))
                        autosave()
                        log(f"Linha {del_id} removida.")
                        st.rerun()
                    except Exception as e:
                        log(str(e), "err"); st.rerun()

        # ── ABA SCHEMA ─────────────────────────────────────
        with tab_schema:
            if not table.col_count:
                st.markdown('<div class="notif notif-inf">Nenhuma coluna definida ainda.</div>', unsafe_allow_html=True)
            else:
                rows_s = "".join(
                    f"<tr><td>{col.name}</td><td>{type_badge(col.dtype.name)}</td>"
                    f"<td>{'✓' if col.nullable else '✗'}</td><td>{'🔒' if col.locked else '—'}</td></tr>"
                    for col in table.columns
                )
                st.markdown(f'<table class="data-table"><thead><tr><th>Nome</th><th>Tipo</th><th>Nullable</th><th>Travado</th></tr></thead><tbody>{rows_s}</tbody></table>', unsafe_allow_html=True)

                st.markdown('<p class="section-title">Renomear coluna</p>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                old_name = c1.selectbox("Coluna:", table.column_names, key="rename_old")
                new_name = c2.text_input("Novo nome:", key="rename_new")
                if st.button("↩ Renomear"):
                    try:
                        table.rename_column(old_name, new_name.strip())
                        autosave(); log(f"'{old_name}' → '{new_name}'."); st.rerun()
                    except Exception as e:
                        log(str(e), "err"); st.rerun()

                st.markdown('<p class="section-title">⚠ Remover coluna</p>', unsafe_allow_html=True)
                rm_col = st.selectbox("Coluna:", table.column_names, key="rm_col")
                if st.button("🗑 Remover coluna"):
                    try:
                        table.remove_column(rm_col)
                        autosave(); log(f"Coluna '{rm_col}' removida."); st.rerun()
                    except Exception as e:
                        log(str(e), "err"); st.rerun()

        # ── ABA STATS ──────────────────────────────────────
        with tab_stats:
            numeric_cols = [n for n, col in table._columns.items() if col.dtype in (DynType.INT, DynType.FLOAT, DynType.AUTO)]
            if not numeric_cols:
                st.markdown('<div class="notif notif-inf">Nenhuma coluna numérica.</div>', unsafe_allow_html=True)
            else:
                rows_st = ""
                for col_name in numeric_cols:
                    s = table.column_stats(col_name)
                    avg_str = f"{s['avg']:.3f}" if s['avg'] is not None else "—"
                    min_str = str(s['min']) if s['min'] is not None else "—"
                    max_str = str(s['max']) if s['max'] is not None else "—"
                    rows_st += f"<tr><td>{col_name}</td><td>{s['count']}</td><td>{s['nulls']}</td><td>{min_str}</td><td>{max_str}</td><td>{avg_str}</td></tr>"
                st.markdown(f'<table class="data-table"><thead><tr><th>Coluna</th><th>Count</th><th>Nulls</th><th>Min</th><th>Max</th><th>Média</th></tr></thead><tbody>{rows_st}</tbody></table>', unsafe_allow_html=True)

        # ── ABA CSV ────────────────────────────────────────
        with tab_csv:
            if table.row_count == 0:
                st.markdown('<div class="notif notif-inf">Nenhuma linha para exportar.</div>', unsafe_allow_html=True)
            else:
                csv_str = table.to_csv_string()
                st.download_button("⬇ Baixar CSV", csv_str.encode("utf-8"), f"{table.name}.csv", "text/csv")
                st.code(csv_str[:2000], language="text")

# ── BARRA LATERAL ─────────────────────────────────────────
with st.sidebar:
    st.markdown('<p style="color:#00ff88;font-size:1.1rem;font-weight:800;font-family:Syne,sans-serif;">⚡ DynTable IoT</p>', unsafe_allow_html=True)

    # ══ GERENCIAR TABELAS ══════════════════════════════════
    st.markdown('<p class="section-title">Tabelas</p>', unsafe_allow_html=True)

    # Lista todas as tabelas como botões de seleção
    all_tables = mgr.list_tables()
    if not all_tables:
        st.markdown('<div class="notif notif-inf" style="font-size:0.75rem">Nenhuma tabela ainda.</div>', unsafe_allow_html=True)
    else:
        for tname in all_tables:
            info = mgr.info(tname)
            is_active = table and table.name == tname
            label = f"{'▶ ' if is_active else ''}{tname}  ({info['row_count']} linhas · {info['col_count']} colunas)"
            if st.button(label, key=f"sel_{tname}", use_container_width=True):
                set_table(mgr.get(tname))
                log(f"Tabela '{tname}' selecionada.", "inf")
                st.rerun()

    st.divider()

    # ── Criar nova tabela ──────────────────────────────────
    st.markdown('<p class="section-title">Nova tabela</p>', unsafe_allow_html=True)
    new_table_name = st.text_input("Nome:", key="new_table_name", placeholder="ex: alertas")
    if st.button("➕ Criar tabela", use_container_width=True):
        name = new_table_name.strip()
        if not name:
            log("Nome não pode ser vazio.", "err")
        else:
            try:
                t = mgr.create(name)
                set_table(t)
                log(f"Tabela '{name}' criada.", "ok")
                st.rerun()
            except TableAlreadyExistsError as e:
                log(str(e), "err"); st.rerun()

    # ── Renomear / deletar tabela ativa ───────────────────
    if table:
        with st.expander("✏ Renomear tabela ativa"):
            rename_val = st.text_input("Novo nome:", key="rename_table_val")
            if st.button("Salvar", key="btn_rename_table"):
                try:
                    new_t = mgr.rename(table.name, rename_val.strip())
                    set_table(new_t)
                    log(f"Tabela renomeada para '{rename_val}'.", "ok")
                    st.rerun()
                except Exception as e:
                    log(str(e), "err"); st.rerun()

        with st.expander("⚠ Deletar tabela ativa"):
            st.markdown('<p style="color:#ff4444;font-size:0.8rem">Isso remove os arquivos do disco permanentemente.</p>', unsafe_allow_html=True)
            if st.button("🗑 Deletar permanentemente", key="btn_del_table"):
                name = table.name
                mgr.delete(name)
                remaining = mgr.list_tables()
                set_table(mgr.get(remaining[0]) if remaining else None)
                log(f"Tabela '{name}' deletada.", "err")
                st.rerun()

    st.divider()

    # ══ OPERAÇÕES NA TABELA ATIVA ══════════════════════════
    if table:

        # ── Adicionar coluna ────────────────────────────────
        st.markdown('<p class="section-title">Nova coluna</p>', unsafe_allow_html=True)
        new_col_name = st.text_input("Nome:", key="new_col_name", placeholder="ex: temperatura_c")
        type_map = {"AUTO":DynType.AUTO,"FLOAT":DynType.FLOAT,"INT":DynType.INT,
                    "STRING":DynType.STRING,"BOOL":DynType.BOOL,"TIMESTAMP":DynType.TIMESTAMP}
        new_col_type     = st.selectbox("Tipo:", list(type_map.keys()), key="new_col_type")
        new_col_nullable = st.checkbox("Nullable", value=True, key="new_col_nullable")

        if st.button("➕ Adicionar coluna", use_container_width=True):
            name = new_col_name.strip()
            if not name:
                log("Nome da coluna não pode ser vazio.", "err")
            else:
                try:
                    table.add_column(name, type_map[new_col_type], new_col_nullable)
                    autosave(); log(f"Coluna '{name}' adicionada."); st.rerun()
                except Exception as e:
                    log(str(e), "err"); st.rerun()

        st.divider()

        # ── Inserir linha ────────────────────────────────────
        st.markdown('<p class="section-title">Nova linha</p>', unsafe_allow_html=True)
        if not table.col_count:
            st.markdown('<div class="notif notif-inf" style="font-size:0.75rem">Adicione colunas primeiro.</div>', unsafe_allow_html=True)
        else:
            row_values = {}
            for col in table.columns:
                dtype = col.dtype
                if dtype in (DynType.FLOAT, DynType.AUTO):
                    v = st.text_input(f"{col.name}:", key=f"ri_{col.name}", placeholder="ex: 23.7")
                    if v.strip():
                        try: row_values[col.name] = float(v)
                        except: row_values[col.name] = v
                elif dtype == DynType.INT:
                    v = st.text_input(f"{col.name}:", key=f"ri_{col.name}", placeholder="ex: 42")
                    if v.strip():
                        try: row_values[col.name] = int(v)
                        except: row_values[col.name] = v
                elif dtype == DynType.BOOL:
                    v = st.selectbox(f"{col.name}:", ["NULL","true","false"], key=f"ri_{col.name}")
                    if v != "NULL": row_values[col.name] = (v == "true")
                elif dtype == DynType.TIMESTAMP:
                    if st.checkbox(f"{col.name} = agora?", key=f"ri_{col.name}"):
                        row_values[col.name] = time.time()
                else:
                    v = st.text_input(f"{col.name}:", key=f"ri_{col.name}")
                    if v.strip(): row_values[col.name] = v

            if st.button("🚀 Inserir linha", use_container_width=True):
                try:
                    row = table.new_row(**row_values)
                    autosave(); log(f"Linha {row.id} inserida."); st.rerun()
                except Exception as e:
                    log(str(e), "err"); st.rerun()

    st.divider()

    # ── Log ──────────────────────────────────────────────
    st.markdown('<p class="section-title">Log</p>', unsafe_allow_html=True)
    for entry in st.session_state.log[:12]:
        st.markdown(
            f'<div class="notif notif-{entry["kind"]}" style="margin:3px 0;font-size:0.72rem;">'
            f'<span style="opacity:0.5">{entry["ts"]}</span>  {entry["msg"]}</div>',
            unsafe_allow_html=True
        )

from __future__ import annotations

import time
import streamlit as st

from dyntable import DynTable, DynType, DuplicateColumnError
from table_manager import TableManager, TableNotFoundError, TableAlreadyExistsError
from ui.styles import type_badge
from config import PASTA_DADOS, TABELA_PADRAO

_TYPE_MAP: dict[str, DynType] = {
    "AUTO":      DynType.AUTO,
    "FLOAT":     DynType.FLOAT,
    "INT":       DynType.INT,
    "STRING":    DynType.STRING,
    "BOOL":      DynType.BOOL,
    "TIMESTAMP": DynType.TIMESTAMP,
}

def _init_state() -> None:
    if "mgr" not in st.session_state:
        st.session_state.mgr = TableManager(PASTA_DADOS)

    mgr: TableManager = st.session_state.mgr
    if "active_table" not in st.session_state:
        if TABELA_PADRAO and mgr.exists(TABELA_PADRAO):
            st.session_state.active_table = mgr.get(TABELA_PADRAO)
        elif mgr.list_tables():
            st.session_state.active_table = mgr.get(mgr.list_tables()[0])
        else:
            st.session_state.active_table = None

    if "log" not in st.session_state:
        st.session_state.log = []

def _mgr() -> TableManager:
    return st.session_state.mgr

def _table() -> DynTable | None:
    return st.session_state.active_table

def _set_table(t: DynTable | None) -> None:
    st.session_state.active_table = t

def _autosave() -> None:
    t = _table()
    if t:
        _mgr().save(t)

def _log(msg: str, kind: str = "ok") -> None:
    ts = time.strftime("%H:%M:%S")
    st.session_state.log.insert(0, {"ts": ts, "msg": msg, "kind": kind})
    if len(st.session_state.log) > 50:
        st.session_state.log.pop()

def _header(table: DynTable | None) -> None:
    label = f"· {table.name}" if table else "· nenhuma tabela"
    st.markdown(f"""
    <div class="main-header">
      <h1>⚡ DynTable IoT
        <span style="font-weight:400;color:#2a5a3a;font-size:1rem">{label}</span>
      </h1>
      <p>MatrixStore n×m · colunas em runtime · múltiplas tabelas · .dyndb</p>
    </div>
    """, unsafe_allow_html=True)

    if table:
        n = table.row_count
        m = table.col_count
        nid = table._store._next_id
        st.markdown(
            f'<div class="matrix-info">'
            f'MatrixStore <span class="hi">{n}×{m}</span> '
            f'&nbsp;|&nbsp; next_id <span class="hi">{nid}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    m1, m2, m3, m4 = st.columns(4)
    mgr = _mgr()
    all_tables = mgr.list_tables()
    null_count = (
        sum(1 for row in table for col in table.column_names if row.cell(col).is_null)
        if table and table.col_count else 0
    )

    for col, val, lbl in [
        (m1, len(all_tables),                         "tabelas"),
        (m2, table.row_count if table else "—",       "linhas"),
        (m3, table.col_count if table else "—",       "colunas"),
        (m4, null_count      if table else "—",       "células null"),
    ]:
        with col:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-val">{val}</div>'
                f'<div class="metric-lbl">{lbl}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

def _tab_data(table: DynTable) -> None:
    if not table.col_count:
        st.markdown('<div class="notif notif-inf">Nenhuma coluna ainda. Adicione na barra lateral.</div>', unsafe_allow_html=True)
        return
    if not table.row_count:
        st.markdown('<div class="notif notif-inf">Nenhuma linha. Use o painel lateral para inserir.</div>', unsafe_allow_html=True)
        return

    filter_col = st.selectbox("Filtrar por coluna:", ["(sem filtro)"] + table.column_names, key="filter_col")
    filter_val = st.text_input("Valor:", key="filter_val") if filter_col != "(sem filtro)" else ""

    headers = "".join(
        f"<th>{n} {type_badge(table._columns[n].dtype.name)}</th>"
        for n in table.column_names
    )
    rows_html = ""
    for row in table:
        if filter_col != "(sem filtro)" and filter_val:
            cell_val = str(row[filter_col]) if row[filter_col] is not None else ""
            if filter_val.lower() not in cell_val.lower():
                continue
        cells = ""
        for col in table.column_names:
            c = row.cell(col)
            if c.is_null:
                cells += '<td class="null-cell">NULL</td>'
            elif c.dtype.name == "BOOL":
                cls = "bool-true" if c.value else "bool-false"
                cells += f'<td class="{cls}">{c.formatted()}</td>'
            else:
                cells += f"<td>{c.formatted()}</td>"
        rows_html += (
            f'<tr>'
            f'<td class="id-cell">{row.id}</td>'
            f'<td class="id-cell">{row.created_at_str}</td>'
            f'{cells}</tr>'
        )

    st.markdown(
        f'<table class="data-table">'
        f'<thead><tr><th>#ID</th><th>criado_em</th>{headers}</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        f'</table>',
        unsafe_allow_html=True,
    )

    st.markdown('<p class="section-title">⚠ Remover linha</p>', unsafe_allow_html=True)
    del_id = st.number_input("ID:", min_value=1, step=1, key="del_row_id")
    if st.button("🗑 Deletar linha"):
        try:
            table.delete_row(int(del_id))
            _autosave()
            _log(f"Linha {del_id} removida.")
            st.rerun()
        except Exception as e:
            _log(str(e), "err"); st.rerun()


def _tab_schema(table: DynTable) -> None:
    if not table.col_count:
        st.markdown('<div class="notif notif-inf">Nenhuma coluna definida ainda.</div>', unsafe_allow_html=True)
        return

    rows_s = "".join(
        f"<tr>"
        f"<td>{col.name}</td>"
        f"<td>{type_badge(col.dtype.name)}</td>"
        f"<td>{'✓' if col.nullable else '✗'}</td>"
        f"<td>{'🔒' if col.locked else '—'}</td>"
        f"</tr>"
        for col in table.columns
    )
    st.markdown(
        f'<table class="data-table">'
        f'<thead><tr><th>Nome</th><th>Tipo</th><th>Nullable</th><th>Travado</th></tr></thead>'
        f'<tbody>{rows_s}</tbody></table>',
        unsafe_allow_html=True,
    )

    st.markdown('<p class="section-title">Renomear coluna</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    old_name = c1.selectbox("Coluna:", table.column_names, key="rename_old")
    new_name = c2.text_input("Novo nome:", key="rename_new")
    if st.button("↩ Renomear"):
        try:
            table.rename_column(old_name, new_name.strip())
            _autosave(); _log(f"'{old_name}' → '{new_name}'."); st.rerun()
        except Exception as e:
            _log(str(e), "err"); st.rerun()

    st.markdown('<p class="section-title">⚠ Remover coluna</p>', unsafe_allow_html=True)
    rm_col = st.selectbox("Coluna:", table.column_names, key="rm_col")
    if st.button("🗑 Remover coluna"):
        try:
            table.remove_column(rm_col)
            _autosave(); _log(f"Coluna '{rm_col}' removida."); st.rerun()
        except Exception as e:
            _log(str(e), "err"); st.rerun()


def _tab_stats(table: DynTable) -> None:
    numeric_cols = [
        n for n, col in table._columns.items()
        if col.dtype in (DynType.INT, DynType.FLOAT, DynType.AUTO)
    ]
    if not numeric_cols:
        st.markdown('<div class="notif notif-inf">Nenhuma coluna numérica.</div>', unsafe_allow_html=True)
        return

    rows_st = ""
    for col_name in numeric_cols:
        s       = table.column_stats(col_name)
        avg_str = f"{s['avg']:.4f}" if s['avg'] is not None else "—"
        min_str = str(s['min'])     if s['min'] is not None else "—"
        max_str = str(s['max'])     if s['max'] is not None else "—"
        rows_st += (
            f"<tr><td>{col_name}</td><td>{s['count']}</td><td>{s['nulls']}</td>"
            f"<td>{min_str}</td><td>{max_str}</td><td>{avg_str}</td></tr>"
        )
    st.markdown(
        f'<table class="data-table">'
        f'<thead><tr><th>Coluna</th><th>Count</th><th>Nulls</th>'
        f'<th>Min</th><th>Max</th><th>Média</th></tr></thead>'
        f'<tbody>{rows_st}</tbody></table>',
        unsafe_allow_html=True,
    )


def _tab_csv(table: DynTable) -> None:
    if table.row_count == 0:
        st.markdown('<div class="notif notif-inf">Nenhuma linha para exportar.</div>', unsafe_allow_html=True)
        return
    csv_str = table.to_csv_string()
    st.download_button("⬇ Baixar CSV", csv_str.encode("utf-8"), f"{table.name}.csv", "text/csv")
    st.code(csv_str[:3000], language="text")

def _sidebar(table: DynTable | None) -> None:
    mgr = _mgr()

    with st.sidebar:
        st.markdown(
            '<p style="color:#00ff88;font-size:1.05rem;font-weight:800;'
            'font-family:Syne,sans-serif;margin-bottom:0">⚡ DynTable IoT</p>'
            '<p style="color:#2a2a2a;font-size:0.65rem;font-family:JetBrains Mono,monospace;'
            'margin-top:2px">MatrixStore · .dyndb</p>',
            unsafe_allow_html=True,
        )

        st.markdown('<p class="section-title">Visualização GIS</p>', unsafe_allow_html=True)
        st.markdown('<div class="qgis-btn">', unsafe_allow_html=True)
        if st.button("🗺 Abrir no QGIS", use_container_width=True, key="btn_open_qgis"):
            try:
                from qgis_bridge.launcher import launch_qgis
                launch_qgis()
                _log("QGIS iniciado.", "inf")
            except FileNotFoundError as e:
                _log(str(e), "err")
            except Exception as e:
                _log(f"Erro: {e}", "err")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="notif notif-inf" style="font-size:0.7rem;margin-top:4px">'
            'QGIS sincroniza automaticamente enquanto estiver aberto.'
            '</div>',
            unsafe_allow_html=True,
        )

        st.divider()

        st.markdown('<p class="section-title">Tabelas</p>', unsafe_allow_html=True)
        all_tables = mgr.list_tables()
        if not all_tables:
            st.markdown(
                '<div class="notif notif-inf" style="font-size:0.72rem">Nenhuma tabela ainda.</div>',
                unsafe_allow_html=True,
            )
        for tname in all_tables:
            info     = mgr.info(tname)
            is_active = table and table.name == tname
            label    = f"{'▶ ' if is_active else ''}{tname}  ({info['row_count']}L · {info['col_count']}C)"
            if st.button(label, key=f"sel_{tname}", use_container_width=True):
                _set_table(mgr.get(tname))
                _log(f"Tabela '{tname}' selecionada.", "inf")
                st.rerun()

        st.divider()

        st.markdown('<p class="section-title">Nova tabela</p>', unsafe_allow_html=True)
        new_table_name = st.text_input("Nome:", key="new_table_name", placeholder="ex: alertas")
        if st.button("➕ Criar tabela", use_container_width=True):
            name = new_table_name.strip()
            if not name:
                _log("Nome não pode ser vazio.", "err")
            else:
                try:
                    t = mgr.create(name)
                    _set_table(t)
                    _log(f"Tabela '{name}' criada.", "ok")
                    st.rerun()
                except TableAlreadyExistsError as e:
                    _log(str(e), "err"); st.rerun()

        if table:
            with st.expander("✏ Renomear tabela ativa"):
                rename_val = st.text_input("Novo nome:", key="rename_table_val")
                if st.button("Salvar", key="btn_rename_table"):
                    try:
                        new_t = mgr.rename(table.name, rename_val.strip())
                        _set_table(new_t)
                        _log(f"Renomeada para '{rename_val}'.", "ok")
                        st.rerun()
                    except Exception as e:
                        _log(str(e), "err"); st.rerun()

            with st.expander("⚠ Deletar tabela ativa"):
                st.markdown(
                    '<p style="color:#ff4444;font-size:0.78rem">'
                    'Remove o arquivo .dyndb permanentemente.</p>',
                    unsafe_allow_html=True,
                )
                if st.button("🗑 Deletar permanentemente", key="btn_del_table"):
                    name = table.name
                    mgr.delete(name)
                    remaining = mgr.list_tables()
                    _set_table(mgr.get(remaining[0]) if remaining else None)
                    _log(f"Tabela '{name}' deletada.", "err")
                    st.rerun()

        st.divider()

        if table:

            st.markdown('<p class="section-title">Nova coluna</p>', unsafe_allow_html=True)
            new_col_name     = st.text_input("Nome:", key="new_col_name", placeholder="ex: temperatura_c")
            new_col_type     = st.selectbox("Tipo:", list(_TYPE_MAP.keys()), key="new_col_type")
            new_col_nullable = st.checkbox("Nullable", value=True, key="new_col_nullable")
            if st.button("➕ Adicionar coluna", use_container_width=True):
                name = new_col_name.strip()
                if not name:
                    _log("Nome da coluna não pode ser vazio.", "err")
                else:
                    try:
                        table.add_column(name, _TYPE_MAP[new_col_type], new_col_nullable)
                        _autosave(); _log(f"Coluna '{name}' adicionada."); st.rerun()
                    except Exception as e:
                        _log(str(e), "err"); st.rerun()

            st.divider()

            st.markdown('<p class="section-title">Nova linha</p>', unsafe_allow_html=True)
            if not table.col_count:
                st.markdown(
                    '<div class="notif notif-inf" style="font-size:0.72rem">Adicione colunas primeiro.</div>',
                    unsafe_allow_html=True,
                )
            else:
                row_values: dict = {}
                for col in table.columns:
                    dtype = col.dtype
                    if dtype in (DynType.FLOAT, DynType.AUTO):
                        v = st.text_input(f"{col.name}:", key=f"ri_{col.name}", placeholder="ex: 23.7")
                        if v.strip():
                            try:    row_values[col.name] = float(v)
                            except: row_values[col.name] = v
                    elif dtype == DynType.INT:
                        v = st.text_input(f"{col.name}:", key=f"ri_{col.name}", placeholder="ex: 42")
                        if v.strip():
                            try:    row_values[col.name] = int(v)
                            except: row_values[col.name] = v
                    elif dtype == DynType.BOOL:
                        v = st.selectbox(f"{col.name}:", ["NULL", "true", "false"], key=f"ri_{col.name}")
                        if v != "NULL":
                            row_values[col.name] = (v == "true")
                    elif dtype == DynType.TIMESTAMP:
                        if st.checkbox(f"{col.name} = agora?", key=f"ri_{col.name}"):
                            row_values[col.name] = time.time()
                    else:
                        v = st.text_input(f"{col.name}:", key=f"ri_{col.name}")
                        if v.strip():
                            row_values[col.name] = v

                if st.button("🚀 Inserir linha", use_container_width=True):
                    try:
                        row = table.new_row(**row_values)
                        _autosave(); _log(f"Linha {row.id} inserida."); st.rerun()
                    except Exception as e:
                        _log(str(e), "err"); st.rerun()

        st.divider()

        st.markdown('<p class="section-title">Log</p>', unsafe_allow_html=True)
        for entry in st.session_state.log[:14]:
            st.markdown(
                f'<div class="notif notif-{entry["kind"]}" style="font-size:0.7rem;">'
                f'<span style="opacity:0.4">{entry["ts"]}</span>  {entry["msg"]}</div>',
                unsafe_allow_html=True,
            )

def _main_panel(table: DynTable | None) -> None:
    if not table:
        st.markdown(
            '<div class="no-table">'
            '<span class="arrow">↙</span>'
            'Nenhuma tabela selecionada.<br>'
            '<span style="font-size:0.85rem;color:#222">Crie uma na barra lateral.</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    tab_data, tab_schema, tab_stats, tab_csv = st.tabs(
        ["📋 Dados", "🗂 Schema", "📊 Estatísticas", "📤 Exportar CSV"]
    )
    with tab_data:   _tab_data(table)
    with tab_schema: _tab_schema(table)
    with tab_stats:  _tab_stats(table)
    with tab_csv:    _tab_csv(table)

def render_app() -> None:
    _init_state()
    table = _table()

    _header(table)

    col_main, col_side = st.columns([3, 1])
    with col_main:
        _main_panel(table)

    _sidebar(table)

/**
 * ui.js — Manipulação do DOM
 * Gêmeo Digital · UNIFACS IoT
 *
 * Responsabilidades:
 *  - Renderizar lista de sensores na sidebar
 *  - Renderizar botões de atributo (auto-introspecção)
 *  - Renderizar legenda
 *  - Atualizar barra de status (status bar)
 *  - Gerenciar seleção de sensor e edição de nome inline
 *  - Relógio em tempo real
 */

import { AC, SENSORS, PENDING_SENSORS, TABLES, activeTable, MKS, attrActive, setAttrActive, sensorColor, reloadData } from './app.js';
import { renderSensors, updateHeatmap, puContent, togLayer, startDefinePosition } from './map.js';
import { fetchStatus, patchSensorName, activateTable, deleteTable } from './api.js';

/* ── ESTADO DA UI ────────────────────────────────────────────────── */
export let selId = null;

/* ── RELÓGIO ─────────────────────────────────────────────────────── */
export function tick() {
  const n = new Date();
  const p = (x) => String(x).padStart(2, '0');
  const el = document.getElementById('clock');
  if (el) el.textContent = `${p(n.getHours())}:${p(n.getMinutes())}:${p(n.getSeconds())}`;
}

/* ── STATUS BAR — substitui o mock por fetch real ───────────────── */
/**
 * Busca /api/v1/status e atualiza o rodapé.
 * Em caso de erro de rede (API indisponível), exibe indicação visual.
 */
export async function loadStatus() {
  const tsEl = document.getElementById('sync-ts');
  const stEl = document.getElementById('sync-s');

  try {
    const data = await fetchStatus();

    if (tsEl) tsEl.textContent = data.ultima_atualizacao ?? '–';

    if (stEl) {
      stEl.textContent   = data.status ?? '–';
      stEl.style.color   = data.status === 'sucesso' ? 'var(--gn)' : 'var(--rd)';
    }
  } catch (err) {
    console.error('[ui] Erro ao carregar status:', err);
    if (tsEl) tsEl.textContent = '–';
    if (stEl) {
      stEl.textContent = 'Erro de Conexão';
      stEl.style.color = 'var(--rd)';
    }
  }
}

/* ── TOPBAR STATS ────────────────────────────────────────────────── */
export function topStats() {
  const on = SENSORS.filter((s) => s.st === 'online').length;
  const al = SENSORS.filter((s) => s.st === 'alert' || s.st === 'warning').length;
  const onEl = document.getElementById('ts-on');
  const alEl = document.getElementById('ts-al');
  if (onEl) onEl.textContent = `${on}/${SENSORS.length}`;
  if (alEl) alEl.textContent = al;
}

/* ── LISTA DE SENSORES (SIDEBAR) ─────────────────────────────────── */
export function renderList() {
  const scEl  = document.getElementById('sc');
  const listEl = document.getElementById('sb-sl');
  if (!listEl) return;

  if (scEl) scEl.textContent = SENSORS.length;

  listEl.innerHTML = SENSORS.map((s) => {
    const v      = s.data[attrActive];
    const u      = AC[attrActive]?.unit ?? '';
    const col    = sensorColor(s);
    const dotCls = s.st === 'alert' ? 'sda' : s.st === 'warning' ? 'sdw' : 'sdo';
    const hasVal = v !== undefined && v !== null && !isNaN(Number(v));
    const displayVal = hasVal ? v : 'N/A';

    return `<div class="si${selId === s.id ? ' sel' : ''}" id="si-${s.id}" onclick="window.__ui.selSensor('${s.id}')">
      <span class="sd-dot ${dotCls}"></span>
      <div class="sn-info">
        <div class="sn-name" title="${s.name}" style="font-weight:600">${s.name}</div>
        <div class="sn-id">${s.id} · ${s.blk}</div>
      </div>
      <div class="sn-val" style="color:${col}">${displayVal}<span style="font-size:9px;color:var(--t2)">${u}</span></div>
    </div>`;
  }).join('');
}

/* ── BOTÕES DE ATRIBUTO ──────────────────────────────────────────── */
/**
 * Renderiza os botões de seleção de variável.
 *
 * Em produção, `attrs` virá do resultado de fetchWFSSchema() (app.js),
 * fazendo autodescoberta real via QGIS Server WFS DescribeFeatureType.
 * Enquanto a integração WFS não estiver pronta, mantém fallback para
 * as chaves do primeiro sensor do array SENSORS.
 *
 * @param {string[]} [attrs] - Lista de atributos descobertos via WFS
 */
export function renderAttrBtns(attrs) {
  const ignored = ['id', 'created_at', 'geometry', 'geom', 'latitude', 'longitude', 'sensor_id', 'name', 'blk', 'st', 'ts'];
  const resolvedAttrs = attrs ?? Object.keys(SENSORS[0]?.data ?? {}).filter(k => !ignored.includes(k.toLowerCase()));
  const acEl  = document.getElementById('ac');
  const agEl  = document.getElementById('ag');
  if (!agEl) return;

  if (acEl) acEl.textContent = resolvedAttrs.length;

  agEl.innerHTML = resolvedAttrs.map((a) => {
    // Fallback dinâmico: se a variável não possui config no AC, gera uma dinâmica e amigável!
    const c = AC[a] ?? {
      lbl: a.replace(/_/g, ' ').toUpperCase(),
      unit: '',
      min: 0,
      max: 100,
      colors: ['#00d4ff','#22c55e','#eab308','#f97316','#ef4444'],
      thr: [20,40,60,80]
    };
    
    const validSensors = SENSORS.filter(s => s.data[a] !== undefined && s.data[a] !== null);
    const avg = validSensors.length > 0 
      ? (validSensors.reduce((t, s) => t + Number(s.data[a]), 0) / validSensors.length).toFixed(1)
      : '0.0';

    return `<button class="ab${a === attrActive ? ' on' : ''}" id="ab-${a}" onclick="window.__ui.setAttr('${a}')">
      <span class="ab-lbl" title="${c.lbl}">${c.lbl}</span>
      <span class="av">${avg}<span class="ab-unit">${c.unit}</span></span>
    </button>`;
  }).join('');
}

/* ── LEGENDA ─────────────────────────────────────────────────────── */
export function renderLegend() {
  const c = AC[attrActive] ?? {
    lbl: attrActive.replace(/_/g, ' ').toUpperCase(),
    unit: '',
    min: 0,
    max: 100,
    colors: ['#00d4ff','#22c55e','#eab308','#f97316','#ef4444'],
    thr: [20,40,60,80]
  };
  const el  = document.getElementById('leg-attr');
  if (!el) return;

  el.innerHTML = `
    <div style="font-size:9px;color:var(--t2);text-transform:uppercase;letter-spacing:.08em;margin-bottom:7px">${c.lbl} (${c.unit})</div>
    <div id="leg-strip" style="height:7px;border-radius:4px;background:linear-gradient(to right,${c.colors.join(',')});margin-bottom:5px"></div>
    <div class="leg-lbl">
      <span class="leg-l">${c.min}</span>
      <span class="leg-l">${c.thr[1]}</span>
      <span class="leg-l">${c.max}</span>
    </div>`;
}

/* ── SELEÇÃO DE ATRIBUTO ─────────────────────────────────────────── */
export function setAttr(a) {
  setAttrActive(a);
  document.querySelectorAll('.ab').forEach((b) => b.classList.remove('on'));
  document.getElementById(`ab-${a}`)?.classList.add('on');
  renderSensors();
  renderList();
  renderLegend();
  const lbl = document.getElementById('wms-lbl');
  if (lbl) {
    lbl.textContent = `WMS GetMap STYLES=${a}`;
    setTimeout(() => { lbl.textContent = 'WMS → QGIS Server :8080'; }, 2500);
  }
}

/* ── SELEÇÃO DE SENSOR ───────────────────────────────────────────── */
export async function selSensor(id) {
  if (selId) document.getElementById(`si-${selId}`)?.classList.remove('sel');
  selId = id;
  const el = document.getElementById(`si-${id}`);
  if (el) { el.classList.add('sel'); el.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }
  const m = MKS[id];
  if (m) {
    const { map } = await import('./map.js').catch(() => ({}));
    map?.setView([m.s.lat, m.s.lng], 16, { animate: true });
    m.mk.openPopup();
  }
}

/* ── EDIÇÃO DE NOME INLINE ──────────────────────────────────────── */
export function initEditName(id) {
  const container = document.getElementById(`pnm-${id}`);
  if (!container) return;

  const currentName = container.textContent.trim();
  container.innerHTML = `<input type="text" class="edit-input" id="inp-${id}" value="${currentName}" onkeydown="if(event.key==='Enter') window.__ui.saveName('${id}')">`;
  document.getElementById(`inp-${id}`)?.focus();

  const btn = document.getElementById(`be-${id}`);
  if (btn) {
    btn.textContent = 'Salvar';
    btn.setAttribute('onclick', `window.__ui.saveName('${id}')`);
  }
}

export async function saveName(id) {
  const inp = document.getElementById(`inp-${id}`);
  if (!inp) return;
  const newName = inp.value.trim();
  if (!newName) return;

  /* Atualiza o array local imediatamente (optimistic update) */
  const s = SENSORS.find((x) => x.id === id);
  if (s) s.name = newName;

  /* Tenta persistir no backend via PATCH */
  try {
    await patchSensorName(id, newName);
  } catch (err) {
    console.warn('[ui] PATCH /sensors falhou (modo offline):', err);
    /* Continua localmente mesmo sem confirmação do backend */
  }

  /* Re-renderiza lista e popup */
  renderList();

  const nameEl = document.getElementById(`pnm-${id}`);
  if (nameEl) nameEl.textContent = newName;

  const btn = document.getElementById(`be-${id}`);
  if (btn) {
    btn.textContent = 'Editar Nome';
    btn.setAttribute('onclick', `window.__ui.initEditName('${id}')`);
  }

  if (MKS[id]) MKS[id].mk.setPopupContent(puContent(MKS[id].s));

  updateHeatmap();
}

/* ── SECTION TOGGLES ─────────────────────────────────────────────── */
export function togSec(id) {
  const b  = document.getElementById(`sb-${id}`);
  const ch = document.getElementById(`ch-${id}`);
  const visible = b?.style.display !== 'none';
  if (b)  b.style.display = visible ? 'none' : '';
  if (ch) ch.classList.toggle('o', !visible);
}

/* ── LISTA DE GEOLOCALIZAÇÃO PENDENTE ────────────────────────────── */
export function renderPendingList() {
  const gpEl = document.getElementById('pending-sensors-list');
  if (!gpEl) return;
  
  if (PENDING_SENSORS.length === 0) {
    gpEl.innerHTML = `<div style="font-size:11px;color:var(--t2);padding:6px;text-align:center">Nenhuma pendência</div>`;
    return;
  }
  
  gpEl.innerHTML = PENDING_SENSORS.map((s) => {
    return `<div style="display:flex;align-items:center;justify-content:space-between;background:var(--bg2);padding:6px 8px;border-radius:4px;margin-bottom:2px;border:1px solid var(--bdr)">
      <div style="flex:1;min-width:0;margin-right:6px">
        <div style="font-weight:600;font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${s.name}">${s.name}</div>
        <div style="font-family:var(--fm);font-size:9px;color:var(--t2)">${s.id}</div>
      </div>
      <button class="btn-edit" onclick="window.__ui.startDefinePosition('${s.id}')" style="padding:2px 6px;font-size:9px;white-space:nowrap">Definir Posição</button>
    </div>`;
  }).join('');
}

/* ── GERENCIAR DATALAKE (TABELAS) ───────────────────────────────── */
export function renderTablesList() {
  const dlEl = document.getElementById('datalake-tables-list');
  if (!dlEl) return;
  
  if (TABLES.length === 0) {
    dlEl.innerHTML = `<div style="font-size:11px;color:var(--t2);padding:6px;text-align:center">Nenhuma tabela</div>`;
    return;
  }
  
  dlEl.innerHTML = TABLES.map((tName) => {
    const isActive = tName === activeTable;
    const activeText = isActive ? 'Ativa' : 'Inativa';
    const activeColor = isActive ? 'var(--gn)' : 'var(--t2)';
    const btnActiveHtml = isActive 
      ? `<span class="badge b-gn" style="font-size:8px;padding:1px 4px">ATIVADA</span>`
      : `<button class="btn-edit" onclick="window.__ui.handleActivateTable('${tName}')" style="padding:2px 6px;font-size:9px">Ativar</button>`;
      
    const btnDeleteHtml = isActive 
      ? `<span style="font-size:11px;color:var(--t2);opacity:0.5;margin-left:4px;cursor:not-allowed" title="Tabela ativa não pode ser excluída">🗑️</span>`
      : `<span onclick="window.__ui.handleDeleteTable('${tName}')" style="font-size:11px;color:var(--rd);margin-left:6px;cursor:pointer;display:inline-block" title="Excluir tabela">🗑️</span>`;

    return `<div style="display:flex;align-items:center;justify-content:space-between;background:var(--bg2);padding:6px 8px;border-radius:4px;margin-bottom:2px;border:1px solid var(--bdr)">
      <div style="flex:1;min-width:0;margin-right:6px">
        <div style="font-weight:600;font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:${isActive ? 'var(--cy)' : 'var(--t0)'}" title="${tName}">${tName}</div>
        <div style="font-size:9px;color:${activeColor}">${activeText}</div>
      </div>
      <div style="display:flex;align-items:center">
        ${btnActiveHtml}
        ${btnDeleteHtml}
      </div>
    </div>`;
  }).join('');
}

export async function handleActivateTable(tableName) {
  try {
    await activateTable(tableName);
    await reloadData();
  } catch (err) {
    console.error('[ui] Erro ao ativar tabela:', err);
    alert(`Erro ao ativar tabela: ${err.message}`);
  }
}

export async function handleDeleteTable(tableName) {
  if (confirm(`Deseja realmente excluir a tabela "${tableName}"? Esta ação não pode ser desfeita.`)) {
    try {
      await deleteTable(tableName);
      await reloadData();
    } catch (err) {
      console.error('[ui] Erro ao deletar tabela:', err);
      alert(`Erro ao deletar tabela: ${err.message}`);
    }
  }
}

/* ── EXPÕE API PÚBLICA PARA CHAMADAS INLINE DO HTML ─────────────── */
window.__ui = {
  selSensor,
  setAttr,
  initEditName,
  saveName,
  togSec,
  togLayer,
  startDefinePosition,
  handleActivateTable,
  handleDeleteTable,
};

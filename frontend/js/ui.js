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

import { AC, SENSORS, MKS, attrActive, setAttrActive, sensorColor } from './app.js';
import { renderSensors, updateHeatmap, puContent, togLayer } from './map.js';
import { fetchStatus, patchSensorName } from './api.js';

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

    return `<div class="si${selId === s.id ? ' sel' : ''}" id="si-${s.id}" onclick="window.__ui.selSensor('${s.id}')">
      <span class="sd-dot ${dotCls}"></span>
      <div class="sn-info">
        <div class="sn-name" title="${s.name}" style="font-weight:600">${s.name}</div>
        <div class="sn-id">${s.id} · ${s.blk}</div>
      </div>
      <div class="sn-val" style="color:${col}">${v}<span style="font-size:9px;color:var(--t2)">${u}</span></div>
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
  const resolvedAttrs = attrs ?? Object.keys(SENSORS[0]?.data ?? {});
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
      <span style="font-size:8px;text-transform:uppercase;letter-spacing:.06em;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:110px;" title="${c.lbl}">${c.lbl}</span>
      <span class="av">${avg}<span style="font-size:8px">${c.unit}</span></span>
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

/* ── EXPÕE API PÚBLICA PARA CHAMADAS INLINE DO HTML ─────────────── */
window.__ui = {
  selSensor,
  setAttr,
  initEditName,
  saveName,
  togSec,
  togLayer,
};

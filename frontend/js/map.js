/**
 * map.js — Lógica de mapa (Leaflet)
 * Gêmeo Digital · UNIFACS IoT
 *
 * Responsabilidades:
 *  - Inicializar o mapa Leaflet
 *  - Registrar camadas no dicionário `activeLayers`
 *  - togLayer() dinâmico (sem blocos if por camada)
 *  - Renderizar marcadores de sensor e mapa de calor
 */

import { AC, attrActive, MKS, SENSORS, sensorColor, attrColor } from './app.js';
import { selSensor } from './ui.js';

/* ── INSTÂNCIAS GLOBAIS DO MAPA ─────────────────────────────────── */
export let map;

/**
 * Dicionário de camadas Leaflet.
 * Cada chave corresponde ao `id` usado nos botões da sidebar.
 * Para adicionar uma nova camada: basta inserir uma entrada aqui.
 * A função togLayer() não precisa de nenhuma alteração.
 */
export let activeLayers = {};

/** Estado de visibilidade por camada (true = visível no mapa) */
export const layerOn = {
  base: true,
  sns:  true,
  heat: false,
  grid: false,
};

/* ── INICIALIZAÇÃO DO MAPA ──────────────────────────────────────── */
export function initMap() {
  map = L.map('mp', {
    center: [-12.9750, -38.4600],
    zoom: 13,
    zoomControl: true,
    attributionControl: true,
  });

  /* ── Dicionário de camadas registradas ─────────────────────────
   *
   * Adicionar uma camada nova = adicionar uma linha aqui.
   * togLayer() funcionará automaticamente para ela.
   * ─────────────────────────────────────────────────────────────*/
  activeLayers = {
    /* Mapa base (CartoDB Dark) */
    base: L.tileLayer(
      'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
      { attribution: '&copy; OSM &copy; CARTO', subdomains: 'abcd', maxZoom: 20 }
    ),

    /* Grupo de marcadores de sensores IoT */
    sns: L.layerGroup(),

    /* Mapa de calor calibrado pela temperatura */
    heat: L.heatLayer([], {
      radius:   45,
      blur:     25,
      maxZoom:  15,
      gradient: {
        0.4: '#00d4ff',
        0.6: '#22c55e',
        0.7: '#eab308',
        0.8: '#f97316',
        1.0: '#ef4444',
      },
    }),

    /**
     * Grade Campus via WMS do QGIS Server.
     * BUG CORRIGIDO: camada 'grid' estava ausente nos if-chains
     * do código original, tornando o botão não-funcional.
     * Agora é tratada automaticamente pelo togLayer() dinâmico.
     */
    grid: L.tileLayer.wms(`${window.QGIS_BASE ?? 'http://localhost:8080'}/wms`, {
      layers:      'grade_campus',
      format:      'image/png',
      transparent: true,
      version:     '1.3.0',
      attribution: 'QGIS Server',
    }),
  };

  /* Adiciona ao mapa as camadas que começam visíveis */
  Object.entries(layerOn).forEach(([id, visible]) => {
    if (visible && activeLayers[id]) {
      activeLayers[id].addTo(map);
    }
  });

  /* Atualiza badge WMS com coordenadas ao mover o mouse */
  map.on('mousemove', (e) => {
    const lbl = document.getElementById('wms-lbl');
    if (lbl) lbl.textContent = `WMS GetMap · ${e.latlng.lat.toFixed(5)}, ${e.latlng.lng.toFixed(5)}`;
  });
  map.on('mouseout', () => {
    const lbl = document.getElementById('wms-lbl');
    if (lbl) lbl.textContent = 'WMS → QGIS Server :8080';
  });
}

/* ── TOGGLE DE CAMADAS (DINÂMICO, SEM IF POR CAMADA) ────────────── */
/**
 * Alterna a visibilidade de uma camada pelo seu ID.
 * Graças ao dicionário `activeLayers`, nenhum bloco `if` específico
 * por camada é necessário — inclusive para a grade GPKG.
 *
 * @param {string} id - Chave do dicionário activeLayers
 */
export function togLayer(id) {
  const layer = activeLayers[id];

  if (!layer) {
    console.warn(`[map] Camada "${id}" não encontrada em activeLayers.`);
    return;
  }

  /* Inverte o estado */
  layerOn[id] = !layerOn[id];

  /* Aplica ao mapa */
  if (map.hasLayer(layer)) {
    map.removeLayer(layer);
  } else {
    map.addLayer(layer);
  }

  /* Sincroniza o checkbox visual na sidebar */
  const ck = document.getElementById(`lc-${id}`);
  if (ck) ck.classList.toggle('on', layerOn[id]);
}

/* ── MARCADORES DE SENSOR ────────────────────────────────────────── */
function mkIcon(s) {
  const col = sensorColor(s);
  const v   = s.data[attrActive];
  const u   = AC[attrActive]?.unit ?? '';
  const ani = s.st === 'alert' ? 'prf .7s' : 'pr 2.4s';

  const html = `
    <div style="position:relative;width:40px;height:40px;">
      <div style="position:absolute;top:0;left:0;width:100%;height:100%;border-radius:50%;border:2px solid ${col};animation:${ani} ease-out infinite;transform-origin:center;opacity:.7;"></div>
      <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:18px;height:18px;border-radius:50%;background:rgba(3,13,28,.75);border:2px solid ${col};display:flex;align-items:center;justify-content:center;">
        <div style="width:6px;height:6px;border-radius:50%;background:${col};"></div>
      </div>
      <div style="position:absolute;top:-16px;left:50%;transform:translateX(-50%);background:rgba(7,21,38,.9);border:1px solid ${col};border-radius:3px;padding:1px 5px;font-family:'JetBrains Mono',monospace;font-size:9px;color:${col};white-space:nowrap;">${v}${u}</div>
    </div>`;

  return L.divIcon({ html, className: '', iconSize: [40, 40], iconAnchor: [20, 20], popupAnchor: [0, -22] });
}

export function puContent(s) {
  const stMap = {
    online:  ['#22c55e', 'Online'],
    warning: ['#f59e0b', 'Alerta'],
    alert:   ['#ef4444', 'Crítico'],
  };
  const [sc, sl] = stMap[s.st] ?? ['#888', 'N/A'];

  const cards = Object.entries(s.data).map(([k, v]) => {
    const c = AC[k];
    if (!c) return '';
    const col = attrColor(k, v);
    return `<div class="pu-card">
      <div class="pu-lbl">${c.lbl}</div>
      <div class="pu-val" style="color:${col}">${v}<span class="pu-unit"> ${c.unit}</span></div>
    </div>`;
  }).join('');

  return `<div class="pu">
    <div class="pu-hd">
      <div>
        <div class="pu-nm" id="pnm-${s.id}">${s.name}</div>
        <div class="pu-id">${s.id} · ${s.blk}</div>
      </div>
      <span class="badge" style="background:transparent;border-color:${sc};color:${sc};padding:2px 7px;font-size:9px;margin-left:8px">${sl}</span>
    </div>
    <div class="pu-grid">${cards}</div>
    <div class="pu-ft">
      <button class="btn-edit" onclick="window.__ui.initEditName('${s.id}')" id="be-${s.id}">Editar Nome</button>
      <span style="font-size:9px;color:var(--t2)">/api/v1/sensors/${s.id}</span>
    </div>
  </div>`;
}

export function renderSensors() {
  const snsLayer = activeLayers.sns;
  if (!snsLayer) return;
  snsLayer.clearLayers();

  SENSORS.forEach((s) => {
    const mk = L.marker([s.lat, s.lng], { icon: mkIcon(s) });
    mk.bindPopup(puContent(s), { maxWidth: 320, className: '' });
    mk.on('click', () => selSensor(s.id));
    snsLayer.addLayer(mk);
    MKS[s.id] = { mk, s };
  });

  updateHeatmap();
}

/* ── MAPA DE CALOR ───────────────────────────────────────────────── */
export function updateHeatmap() {
  const heatLayer = activeLayers.heat;
  if (!heatLayer) return;

  const { min, max } = AC.temperatura;
  const points = SENSORS.map((s) => {
    const intensity = (s.data.temperatura - min) / (max - min);
    return [s.lat, s.lng, intensity];
  });
  heatLayer.setLatLngs(points);
}

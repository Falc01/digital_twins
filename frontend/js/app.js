/**
 * app.js — Ponto de entrada e estado global
 * Gêmeo Digital · UNIFACS IoT
 *
 * Responsabilidades:
 *  - Declarar o estado compartilhado (SENSORS, AC, MKS, attrActive)
 *  - Orquestrar a sequência de boot (loading screen)
 *  - Inicializar todos os módulos na ordem correta
 *  - Executar autodescoberta WFS e injetar resultado em renderAttrBtns()
 */

import { initMap, renderSensors, togLayer } from './map.js';
import { fetchSensors, fetchStatus, fetchWFSSchema } from './api.js';
import {
  renderList, renderAttrBtns, renderLegend,
  topStats, loadStatus, tick, togSec,
} from './ui.js';

/* ══════════════════════════════════════════════════════
   ESTADO GLOBAL — exportado para os outros módulos
   ══════════════════════════════════════════════════════ */

/**
 * SENSORS: array principal de sensores.
 *
 * Em produção este array é preenchido pelo fetchSensors().
 * O mock abaixo serve como fallback offline para desenvolvimento local.
 *
 * TODO: remover o mock quando a rota GET /api/v1/sensors estiver disponível.
 */
export let SENSORS = [];

/**
 * AC (Attribute Config): metadados de cada variável de sensor.
 * Define labels, unidades, faixas e gradientes de cor.
 *
 * Em produção, a lista de chaves de AC deveria ser derivada do
 * esquema WFS (fetchWFSSchema). Os thresholds e cores continuam
 * sendo configuração de frontend.
 */
export const AC = {
  temperatura:  { lbl: 'Temperatura', unit: '°C',  min: 15,   max: 40,    colors: ['#00d4ff','#22c55e','#eab308','#f97316','#ef4444'], thr: [20,25,30,35]     },
  umidade:      { lbl: 'Umidade',     unit: '%',   min: 30,   max: 95,    colors: ['#ef4444','#f97316','#22c55e','#00d4ff','#6366f1'], thr: [40,55,70,85]     },
  co2:          { lbl: 'CO₂',         unit: 'ppm', min: 350,  max: 1500,  colors: ['#22c55e','#84cc16','#eab308','#f97316','#ef4444'], thr: [450,600,800,1000] },
  luminosidade: { lbl: 'Luminosidade',unit: 'lux', min: 0,    max: 10000, colors: ['#1e3a5f','#4f46e5','#8b5cf6','#f59e0b','#fde68a'], thr: [100,500,1500,4000] },
  ruido:        { lbl: 'Ruído',       unit: 'dB',  min: 20,   max: 90,    colors: ['#22c55e','#84cc16','#eab308','#f97316','#ef4444'], thr: [40,55,65,75]     },
};

/** Atributo atualmente selecionado para visualização */
export let attrActive = 'temperatura';
export function setAttrActive(a) { attrActive = a; }

/** Mapa de marcadores Leaflet por sensor ID */
export const MKS = {};

/* ══════════════════════════════════════════════════════
   HELPERS DE COR — exportados para map.js e ui.js
   ══════════════════════════════════════════════════════ */
export function attrColor(attr, v) {
  const c = AC[attr];
  if (!c) return '#00d4ff';
  const t = c.thr, cl = c.colors;
  if (v < t[0]) return cl[0];
  if (v < t[1]) return cl[1];
  if (v < t[2]) return cl[2];
  if (v < t[3]) return cl[3];
  return cl[4];
}

export function sensorColor(s) {
  if (s.st === 'alert')   return '#ef4444';
  if (s.st === 'warning') return '#f59e0b';
  return attrColor(attrActive, s.data[attrActive]);
}

/* ══════════════════════════════════════════════════════
   LOADING SCREEN (boot sequence)
   ══════════════════════════════════════════════════════ */
function boot() {
  const steps = [
    [0,   'Inicializando sistema...'],
    [18,  'Conectando ao QGIS Server WMS...'],
    [36,  'Carregando GeoPackage .gpkg...'],
    [55,  'Autodescoberta de atributos WFS...'],
    [74,  'Carregando sensores IoT...'],
    [92,  'Renderizando mapa...'],
    [100, 'Sistema pronto.'],
  ];
  const bar = document.getElementById('lbar');
  const msg = document.getElementById('lmsg');

  steps.forEach(([p, t], i) => {
    setTimeout(() => {
      if (bar) bar.style.width = `${p}%`;
      if (msg) msg.textContent = t;
    }, i * 180);
  });

  /* Remove a tela de loading após a animação */
  setTimeout(
    () => document.getElementById('ld')?.classList.add('gone'),
    steps.length * 180 + 100,
  );
}

/* ══════════════════════════════════════════════════════
   DADOS MOCK — fallback offline
   Remove este bloco quando GET /api/v1/sensors estiver ativo.
   ══════════════════════════════════════════════════════ */
const SENSORS_MOCK = [
  { id:'SNS-001', name:'Sensor 1',  blk:'Centro Histórico',        lat:-12.9714, lng:-38.5101, data:{temperatura:31.4,umidade:74.2,co2:610, luminosidade:2800,ruido:72}, st:'online',  ts:'20:00' },
  { id:'SNS-002', name:'Sensor 2',  blk:'Barra',                   lat:-13.0106, lng:-38.5323, data:{temperatura:29.8,umidade:82.5,co2:398, luminosidade:5200,ruido:58}, st:'online',  ts:'20:00' },
  { id:'SNS-003', name:'Sensor 3',  blk:'Ondina',                  lat:-13.0003, lng:-38.5173, data:{temperatura:28.9,umidade:80.1,co2:412, luminosidade:4100,ruido:65}, st:'online',  ts:'20:00' },
  { id:'SNS-004', name:'Sensor 4',  blk:'Rio Vermelho',            lat:-13.0059, lng:-38.5026, data:{temperatura:30.5,umidade:77.8,co2:455, luminosidade:3600,ruido:61}, st:'online',  ts:'20:00' },
  { id:'SNS-005', name:'Sensor 5',  blk:'Pituba',                  lat:-12.9939, lng:-38.4561, data:{temperatura:24.2,umidade:62.3,co2:890, luminosidade:420, ruido:68}, st:'warning', ts:'20:00' },
  { id:'SNS-006', name:'Sensor 6',  blk:'Pituba',                  lat:-12.9893, lng:-38.4621, data:{temperatura:32.1,umidade:71.0,co2:385, luminosidade:7800,ruido:42}, st:'online',  ts:'20:00' },
  { id:'SNS-007', name:'Sensor 7',  blk:'Stiep',                   lat:-12.9877, lng:-38.4561, data:{temperatura:31.8,umidade:65.5,co2:540, luminosidade:2900,ruido:70}, st:'online',  ts:'20:00' },
  { id:'SNS-008', name:'Sensor 8',  blk:'Cabula',                  lat:-12.9377, lng:-38.4672, data:{temperatura:34.2,umidade:60.8,co2:720, luminosidade:6100,ruido:74}, st:'warning', ts:'19:30' },
  { id:'SNS-009', name:'Sensor 9',  blk:'Itapuã',                  lat:-12.9289, lng:-38.3622, data:{temperatura:30.1,umidade:85.2,co2:372, luminosidade:9200,ruido:52}, st:'online',  ts:'20:00' },
  { id:'SNS-010', name:'Sensor 10', blk:'Luís Eduardo Magalhães',  lat:-12.9086, lng:-38.3229, data:{temperatura:32.7,umidade:63.1,co2:980, luminosidade:5500,ruido:95}, st:'warning', ts:'20:00' },
  { id:'SNS-011', name:'Sensor 11', blk:'Ribeira',                 lat:-12.9136, lng:-38.5036, data:{temperatura:29.5,umidade:83.7,co2:430, luminosidade:3800,ruido:55}, st:'online',  ts:'20:00' },
];

/* ══════════════════════════════════════════════════════
   INIT — orquestrador principal
   ══════════════════════════════════════════════════════ */
async function init() {
  /* 1. Carrega sensores do backend; cai para mock se API offline */
  try {
    const data = await fetchSensors();
    SENSORS.push(...data);
    console.info(`[app] ${SENSORS.length} sensores carregados da API.`);
  } catch (err) {
    console.warn('[app] API de sensores indisponível — usando mock local:', err);
    SENSORS.push(...SENSORS_MOCK);
  }

  /* 2. Inicializa o mapa Leaflet */
  initMap();

  /* 3. Autodescoberta de atributos via WFS DescribeFeatureType */
  let wfsAttrs = null;
  try {
    let activeTable = 'sensor_readings_demo';
    try {
      const statusData = await fetchStatus();
      if (statusData.tabela) {
        activeTable = statusData.tabela;
      }
    } catch (e) {
      console.warn('[app] Falha ao ler tabela ativa do status:', e);
    }

    const typeName = activeTable.replace(/ /g, '_');
    const props  = await fetchWFSSchema(typeName);
    /* Filtra apenas as propriedades numéricas relevantes (xsd:double, xsd:int) */
    wfsAttrs = props
      .filter((p) => p.type?.includes('double') || p.type?.includes('int'))
      .map((p) => p.name)
      .filter((name) => name in AC);              /* mantém só os que têm config em AC */
    console.info('[app] Atributos WFS descobertos:', wfsAttrs);
  } catch (err) {
    console.warn('[app] WFS DescribeFeatureType indisponível — usando introspecção local:', err);
    /* Fallback: lê as chaves do primeiro sensor (comportamento original) */
    wfsAttrs = null;
  }

  /* 4. Renderiza todos os componentes visuais */
  renderSensors();
  renderList();
  renderAttrBtns(wfsAttrs);   /* passa null para fallback automático */
  renderLegend();
  topStats();

  /* 5. Carrega status do backend */
  await loadStatus();

  /* 6. Inicia relógio */
  tick();
  setInterval(tick, 1000);

  /* 7. Polling de status a cada 60s (alinhado com intervalo WAL do FastAPI) */
  setInterval(loadStatus, 60_000);
}

/* ── BOOTSTRAP ───────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  boot();
  /* Aguarda 400ms para a animação de boot antes de inicializar */
  setTimeout(init, 400);
});

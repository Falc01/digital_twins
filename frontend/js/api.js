/**
 * api.js — Camada de comunicação HTTP
 * Gêmeo Digital · UNIFACS IoT
 *
 * Responsabilidade: consumir endpoints REST do FastAPI e do QGIS Server.
 * Este módulo NÃO cria rotas nem acessa o datalake diretamente.
 * Toda comunicação acontece via fetch() sobre HTTP.
 */

/* ── BASE URLs (ajuste conforme o ambiente) ─────────────────────── */
export const API_BASE   = '/api/v1';
export const QGIS_BASE  = 'http://localhost:8080';

/* ── STATUS · GET /api/v1/status ───────────────────────────────── */
/**
 * Busca telemetria de sincronização do backend FastAPI.
 * Retorna: { ultima_atualizacao: string, status: string,
 *             proxima_atualizacao: string, registros: number, gpkg: string }
 */
export async function fetchStatus() {
  const res = await fetch(`${API_BASE}/status`);
  if (!res.ok) throw new Error(`HTTP ${res.status} em /api/v1/status`);
  return res.json();
}

/* ── SENSORES · GET /api/v1/sensors ────────────────────────────── */
/**
 * Busca a lista completa de sensores com posição e telemetria.
 * Retorna: Array<{ id, name, blk, lat, lng, data: {}, st, ts }>
 */
export async function fetchSensors() {
  const res = await fetch(`${API_BASE}/sensors`);
  if (!res.ok) throw new Error(`HTTP ${res.status} em /api/v1/sensors`);
  return res.json();
}

/* ── SENSOR INDIVIDUAL · GET /api/v1/sensors/:id ───────────────── */
/**
 * Busca um único sensor pelo ID.
 * Retorna: { id, name, blk, lat, lng, data: {}, st, ts }
 */
export async function fetchSensorById(id) {
  const res = await fetch(`${API_BASE}/sensors/${encodeURIComponent(id)}`);
  if (!res.ok) throw new Error(`HTTP ${res.status} em /api/v1/sensors/${id}`);
  return res.json();
}

/* ── PATCH NOME · PATCH /api/v1/sensors/:id ────────────────────── */
/**
 * Persiste a renomeação de um sensor no backend.
 * Retorna: { id, name } com o nome atualizado.
 */
export async function patchSensorName(id, newName) {
  const res = await fetch(`${API_BASE}/sensors/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: newName }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} ao renomear ${id}`);
  return res.json();
}

/* ── WFS DescribeFeatureType · QGIS Server ──────────────────────── */
/**
 * Autodescobre o esquema de atributos de uma camada WFS.
 * O QGIS Server retorna um JSON com as propriedades da tabela,
 * eliminando o acoplamento entre o frontend e o banco de dados.
 *
 * @param {string} typeName - Nome da camada (ex: 'sensores')
 * @returns {Promise<Array<{ name: string, type: string }>>}
 */
export async function fetchWFSSchema(typeName = 'sensores') {
  const url = new URL(`${QGIS_BASE}/wfs`);
  url.searchParams.set('SERVICE',      'WFS');
  url.searchParams.set('VERSION',      '2.0.0');
  url.searchParams.set('REQUEST',      'DescribeFeatureType');
  url.searchParams.set('OUTPUTFORMAT', 'application/json');
  url.searchParams.set('TYPENAME',     typeName);

  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`WFS DescribeFeatureType falhou: HTTP ${res.status}`);

  const json = await res.json();

  /*
   * Estrutura esperada do QGIS Server (OGC WFS 2.0):
   * {
   *   "featureTypes": [{
   *     "typeName": "sensores",
   *     "properties": [{ "name": "temperatura", "type": "xsd:double" }, ...]
   *   }]
   * }
   */
  const featureType = json?.featureTypes?.[0];
  if (!featureType) throw new Error('Resposta WFS sem featureTypes.');

  return featureType.properties ?? [];
}

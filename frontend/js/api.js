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
export const QGIS_BASE  = window.location.origin;

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

/* ── PATCH SENSOR · PATCH /api/v1/sensors/:id ───────────────────── */
/**
 * Persiste atualizações de campos de um sensor no backend (ex: nome, lat, lng).
 * Retorna: { id, name, lat, lng } atualizado.
 */
export async function patchSensor(id, fields) {
  const res = await fetch(`${API_BASE}/sensors/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(fields),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} ao atualizar sensor ${id}`);
  return res.json();
}

/**
 * Persiste a renomeação de um sensor no backend.
 */
export async function patchSensorName(id, newName) {
  return patchSensor(id, { name: newName });
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

/* ── DATALAKE TABLES · GET /api/v1/tables ───────────────────────── */
/**
 * Busca todas as tabelas dinâmicas do DataLake.
 * Retorna: { tables: string[] }
 */
export async function fetchTables() {
  const res = await fetch(`${API_BASE}/tables`);
  if (!res.ok) throw new Error(`HTTP ${res.status} em /api/v1/tables`);
  return res.json();
}

/* ── ACTIVATE TABLE · POST /api/v1/tables/:name/active ──────────── */
/**
 * Muda a fonte de dados ativa do DataLake.
 */
export async function activateTable(tableName) {
  const res = await fetch(`${API_BASE}/tables/${encodeURIComponent(tableName)}/active`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} ao ativar tabela ${tableName}`);
  return res.json();
}

/* ── DELETE TABLE · DELETE /api/v1/tables/:name ─────────────────── */
/**
 * Exclui uma tabela dinâmica do DataLake.
 */
export async function deleteTable(tableName) {
  const res = await fetch(`${API_BASE}/tables/${encodeURIComponent(tableName)}`, {
    method: 'DELETE',
  });
  if (!res.ok && res.status !== 204) throw new Error(`HTTP ${res.status} ao deletar tabela ${tableName}`);
  return true;
}

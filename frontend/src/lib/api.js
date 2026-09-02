import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

const client = axios.create({ baseURL: API });

export const api = {
  health: () => client.get('/health').then((r) => r.data),
  excelSummary: () => client.get('/meta/excel-summary').then((r) => r.data),
  periods: () => client.get('/meta/periods').then((r) => r.data),
  reseed: () => client.post('/admin/reseed').then((r) => r.data),
  listReagen: (query) => client.get('/reagen', { params: { query } }).then((r) => r.data),
  updateReagen: (id, body) => client.put(`/reagen/${id}`, body).then((r) => r.data),
  createReagen: (body) => client.post('/reagen', body).then((r) => r.data),
  monitoring: (year, month) => client.get('/monitoring', { params: { year, month } }).then((r) => r.data),
  setSaldoAwal: (body) => client.put('/monitoring/saldo-awal', body).then((r) => r.data),
  setQc: (body) => client.put('/monitoring/qc', body).then((r) => r.data),
  setSisaOverride: (body) => client.put('/monitoring/sisa-override', body).then((r) => r.data),
  autoSaldoAwal: (year, month) => client.post('/monitoring/auto-saldo-awal', { year, month }).then((r) => r.data),
  mappingTests: (status) => client.get('/mapping-tests', { params: { status } }).then((r) => r.data),
  updateMapping: (id, body) => client.put(`/mapping-tests/${id}`, body).then((r) => r.data),
  lisSourceFiles: (period) => client.get('/lis/source-files', { params: { period } }).then((r) => r.data),
  deleteLisSourceFile: (sf) => client.delete(`/lis/source-file/${encodeURIComponent(sf)}`).then((r) => r.data),
  lisRaw: (period, limit = 300, skip = 0) => client.get('/lis/raw', { params: { period, limit, skip } }).then((r) => r.data),
  lisImport: (fileList) => {
    const fd = new FormData();
    Array.from(fileList).forEach((f) => fd.append('files', f));
    return client.post('/lis/import', fd, { headers: { 'Content-Type': 'multipart/form-data' } }).then((r) => r.data);
  },
  prf: (period) => client.get('/prf', { params: { period } }).then((r) => r.data),
  createPrf: (body) => client.post('/prf', body).then((r) => r.data),
  receivePrf: (id, body) => client.post(`/prf/${id}/terima`, body).then((r) => r.data),
  deletePrf: (id) => client.delete(`/prf/${id}`).then((r) => r.data),
  penerimaan: (period) => client.get('/penerimaan', { params: { period } }).then((r) => r.data),
};

export const MONTHS_ID = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];

export const fmtNum = (v) => {
  if (v === null || v === undefined || v === '') return '-';
  if (typeof v === 'number') return new Intl.NumberFormat('id-ID').format(v);
  return v;
};

export const fmtDate = (s) => {
  if (!s) return '-';
  try {
    const d = new Date(s);
    return d.toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' });
  } catch (e) {
    return s;
  }
};

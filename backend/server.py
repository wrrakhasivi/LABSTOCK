"""LabStock backend – Sistem Pemantauan Stok Reagen Laboratorium PK."""
import os
import re
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict
from starlette.middleware.cors import CORSMiddleware

from database import (
    reagen_col, stock_period_col, pemakaian_col, penerimaan_col,
    prf_col, mapping_col, lis_raw_col, import_log_col,
)
from calculations import build_row, days_in_month, STATUS_LABEL
from excel_analysis import EXCEL_SUMMARY
from seeder import run_seed, is_seeded
from lis_import import import_files as lis_import_files
from export_excel import build_workbook
import whatsapp as wa

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('labstock')

app = FastAPI(title='LabStock API')
api = APIRouter(prefix='/api')

MONTH_NAMES_ID = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']


# ---------- Models ----------
class ReagenUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    nama_reagen: Optional[str] = None
    item_code: Optional[str] = None
    qty_per_kit: Optional[float] = None
    avg_2022: Optional[float] = None
    avg_2023: Optional[float] = None
    buffer_stock: Optional[float] = None
    satuan: Optional[str] = None
    aktif: Optional[bool] = None


class ReagenCreate(BaseModel):
    nama_reagen: str
    item_code: Optional[str] = None
    qty_per_kit: Optional[float] = None
    avg_2022: Optional[float] = None
    avg_2023: Optional[float] = None
    buffer_stock: Optional[float] = None
    satuan: Optional[str] = 'Pcs'


# ---------- Helpers ----------
async def _mapped_reagen_ids():
    """Set id reagen yang memiliki minimal satu pemetaan status OK di Pemetaan Test.

    Reagen tanpa pemetaan (belum dipetakan / TIDAK ADA) tidak dianggap termonitor
    dan disembunyikan dari daftar Pemantauan Stok, Master Reagen, PRF, & Penerimaan.
    """
    names = await mapping_col.distinct('reagen_name',
                                       {'status': 'OK', 'reagen_name': {'$ne': None}})
    names = [n for n in names if n]
    if not names:
        return set()
    docs = await reagen_col.find({'nama_reagen': {'$in': names}},
                                 {'_id': 0, 'id': 1}).to_list(5000)
    return {d['id'] for d in docs}


# ---------- Meta ----------
@api.get('/')
async def root():
    return {'app': 'LabStock', 'message': 'Sistem Pemantauan Stok Reagen Lab PK'}


@api.get('/health')
async def health():
    return {'status': 'ok', 'seeded': await is_seeded()}


@api.get('/meta/excel-summary')
async def excel_summary():
    return EXCEL_SUMMARY


@api.get('/meta/periods')
async def periods():
    """Distinct (year, month) available from stock_period, plus month name."""
    docs = await stock_period_col.find({}, {'_id': 0, 'year': 1, 'month': 1}).to_list(5000)
    seen = sorted({(d['year'], d['month']) for d in docs}, reverse=True)
    return [{'year': y, 'month': m, 'label': f'{MONTH_NAMES_ID[m]} {y}'} for y, m in seen]


@api.post('/admin/reseed')
async def reseed():
    res = await run_seed(force=True)
    return res


# ---------- Master Reagen ----------
@api.get('/reagen')
async def list_reagen(query: Optional[str] = None):
    filt = {}
    if query:
        filt['nama_reagen'] = {'$regex': query, '$options': 'i'}
    docs = await reagen_col.find(filt, {'_id': 0}).sort('nama_reagen', 1).to_list(2000)
    mapped = await _mapped_reagen_ids()
    docs = [d for d in docs if d['id'] in mapped]
    return docs


@api.post('/reagen')
async def create_reagen(payload: ReagenCreate):
    import uuid
    existing = await reagen_col.find_one({'nama_reagen': payload.nama_reagen})
    if existing:
        raise HTTPException(400, 'Nama reagen sudah ada')
    doc = payload.model_dump()
    doc['id'] = str(uuid.uuid4())
    doc['aktif'] = True
    doc['created_at'] = datetime.now(timezone.utc).isoformat()
    await reagen_col.insert_one(doc)
    doc.pop('_id', None)
    return doc


@api.put('/reagen/{reagen_id}')
async def update_reagen(reagen_id: str, payload: ReagenUpdate):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, 'Tidak ada perubahan')
    res = await reagen_col.update_one({'id': reagen_id}, {'$set': updates})
    if res.matched_count == 0:
        raise HTTPException(404, 'Reagen tidak ditemukan')
    doc = await reagen_col.find_one({'id': reagen_id}, {'_id': 0})
    return doc


# ---------- Monitoring (core) ----------
async def _compute_monitoring(year: int, month: int):
    reagens = await reagen_col.find({}, {'_id': 0}).sort('nama_reagen', 1).to_list(3000)
    mapped = await _mapped_reagen_ids()
    reagens = [r for r in reagens if r['id'] in mapped]

    periods_docs = await stock_period_col.find(
        {'year': year, 'month': month}, {'_id': 0}).to_list(3000)
    period_by_reagen = {p['reagen_id']: p for p in periods_docs}

    prefix = f'{year}-{month:02d}-'
    # Daily usage (kolom 1-31) bersumber dari LIS mentah -> Pemetaan Test (status OK)
    # -> Pemantauan Stok. Dihitung dinamis agar perubahan pemetaan langsung tercermin.
    ok_maps = await mapping_col.find(
        {'status': 'OK', 'reagen_name': {'$ne': None}},
        {'_id': 0, 'lis_name': 1, 'reagen_name': 1}).to_list(5000)
    lis_to_reagen = {}
    for m in ok_maps:
        ln = (m.get('lis_name') or '').strip().lower()
        if ln:
            lis_to_reagen[ln] = (m.get('reagen_name') or '').strip()
    name_to_id = {(r['nama_reagen'] or '').strip().lower(): r['id'] for r in reagens}

    period_str = f'{year}-{month:02d}'
    lis_docs = await lis_raw_col.find({'period': period_str}, {'_id': 0}).to_list(50000)
    daily_by_reagen = {}
    for doc in lis_docs:
        lname = (doc.get('nama_test') or '').strip().lower()
        rname = lis_to_reagen.get(lname)
        if not rname and lname in name_to_id:
            rname = (doc.get('nama_test') or '').strip()
        rid = name_to_id.get((rname or '').strip().lower()) if rname else None
        if not rid:
            continue
        dd = daily_by_reagen.setdefault(rid, {})
        for day_str, jumlah in (doc.get('days') or {}).items():
            try:
                day = int(day_str)
            except (ValueError, TypeError):
                continue
            dd[day] = dd.get(day, 0) + (jumlah or 0)

    period_str = f'{year}-{month:02d}'
    pen_docs = await penerimaan_col.find({'period': period_str}, {'_id': 0}).to_list(5000)
    pen_by_reagen = {}
    stok_masuk_by_reagen = {}
    for p in pen_docs:
        pen_by_reagen.setdefault(p['reagen_id'], []).append(p)
        stok_masuk_by_reagen[p['reagen_id']] = stok_masuk_by_reagen.get(p['reagen_id'], 0) + (p.get('qty') or 0)

    prf_docs = await prf_col.find({'period': period_str}, {'_id': 0}).to_list(5000)
    prf_by_reagen = {}
    for p in prf_docs:
        prf_by_reagen.setdefault(p['reagen_id'], []).append(p)

    rows = []
    for r in reagens:
        rid = r['id']
        row = build_row(
            r,
            period_by_reagen.get(rid),
            daily_by_reagen.get(rid, {}),
            stok_masuk_by_reagen.get(rid, 0),
            prf_by_reagen.get(rid, []),
            pen_by_reagen.get(rid, []),
            year, month,
        )
        rows.append(row)

    counts = {'critical': 0, 'warning': 0, 'safe': 0, 'unknown': 0}
    for row in rows:
        counts[row['status']] += 1

    return {
        'year': year,
        'month': month,
        'label': f'{MONTH_NAMES_ID[month]} {year}',
        'days': days_in_month(year, month),
        'counts': counts,
        'total_reagen': len(rows),
        'rows': rows,
    }


@api.get('/monitoring')
async def monitoring(year: int, month: int):
    if month < 1 or month > 12:
        raise HTTPException(400, 'Bulan tidak valid')
    return await _compute_monitoring(year, month)


async def _upsert_period_field(reagen_id: str, year: int, month: int, field: str, value):
    """Set a single field on a (reagen, year, month) stock_period, creating it if needed."""
    existing = await stock_period_col.find_one({'reagen_id': reagen_id, 'year': year, 'month': month})
    if existing:
        await stock_period_col.update_one(
            {'reagen_id': reagen_id, 'year': year, 'month': month},
            {'$set': {field: value}})
    else:
        import uuid
        doc = {
            'id': str(uuid.uuid4()), 'reagen_id': reagen_id, 'year': year, 'month': month,
            'saldo_awal': None, 'qc': 0, 'buffer_override': None, 'sisa_override': None,
            'created_at': datetime.now(timezone.utc).isoformat(),
        }
        doc[field] = value
        await stock_period_col.insert_one(doc)


class SaldoAwalUpdate(BaseModel):
    reagen_id: str
    year: int
    month: int
    saldo_awal: Optional[float] = None


class SisaOverrideUpdate(BaseModel):
    reagen_id: str
    year: int
    month: int
    sisa_override: Optional[float] = None


class QcUpdate(BaseModel):
    reagen_id: str
    year: int
    month: int
    qc: Optional[float] = None


@api.put('/monitoring/qc')
async def set_qc(payload: QcUpdate):
    """Input manual QC untuk sebuah reagen pada periode tertentu."""
    if payload.month < 1 or payload.month > 12:
        raise HTTPException(400, 'Bulan tidak valid')
    await _upsert_period_field(payload.reagen_id, payload.year, payload.month,
                               'qc', payload.qc or 0)
    return {'ok': True}


@api.put('/monitoring/saldo-awal')
async def set_saldo_awal(payload: SaldoAwalUpdate):
    """Manual edit of Saldo Awal for a reagen in a period."""
    if payload.month < 1 or payload.month > 12:
        raise HTTPException(400, 'Bulan tidak valid')
    await _upsert_period_field(payload.reagen_id, payload.year, payload.month,
                               'saldo_awal', payload.saldo_awal)
    return {'ok': True}


@api.put('/monitoring/sisa-override')
async def set_sisa_override(payload: SisaOverrideUpdate):
    """Manual adjustment (override) of Sisa Stok. Pass null to clear and revert to auto."""
    if payload.month < 1 or payload.month > 12:
        raise HTTPException(400, 'Bulan tidak valid')
    await _upsert_period_field(payload.reagen_id, payload.year, payload.month,
                               'sisa_override', payload.sisa_override)
    return {'ok': True}


class AutoSaldoBody(BaseModel):
    year: int
    month: int


@api.post('/monitoring/auto-saldo-awal')
async def auto_saldo_awal(payload: AutoSaldoBody):
    """Isi Saldo Awal bulan ini otomatis = Sisa Stok bulan sebelumnya (per reagen)."""
    year, month = payload.year, payload.month
    if month < 1 or month > 12:
        raise HTTPException(400, 'Bulan tidak valid')
    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    prev = await _compute_monitoring(prev_year, prev_month)
    updated = 0
    for row in prev['rows']:
        sisa = row.get('sisa_stock')
        if sisa is None:
            continue
        await _upsert_period_field(row['reagen_id'], year, month, 'saldo_awal', sisa)
        updated += 1
    return {'ok': True, 'updated': updated,
            'from_period': f'{MONTH_NAMES_ID[prev_month]} {prev_year}'}


@api.post('/monitoring/periode-baru')
async def buat_periode_baru(payload: AutoSaldoBody):
    """Buat periode bulan berikutnya; Saldo Awal = Sisa Stok bulan ini (per reagen).

    Desember -> Januari tahun berikutnya (tahun baru otomatis).
    """
    year, month = payload.year, payload.month
    if month < 1 or month > 12:
        raise HTTPException(400, 'Bulan tidak valid')
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    existed = await stock_period_col.count_documents({'year': next_year, 'month': next_month})
    cur = await _compute_monitoring(year, month)
    created = 0
    for row in cur['rows']:
        await _upsert_period_field(row['reagen_id'], next_year, next_month,
                                   'saldo_awal', row.get('sisa_stock'))
        created += 1
    return {'ok': True, 'year': next_year, 'month': next_month,
            'label': f'{MONTH_NAMES_ID[next_month]} {next_year}',
            'reagen': created, 'already_existed': existed > 0,
            'from_period': f'{MONTH_NAMES_ID[month]} {year}'}


@api.get('/monitoring/periode-info')
async def periode_info(year: int, month: int):
    """Info sebelum hapus periode: jumlah stock_period, data LIS, PRF & penerimaan."""
    period = f'{year}-{month:02d}'
    return {
        'label': f'{MONTH_NAMES_ID[month]} {year}',
        'stock_period': await stock_period_col.count_documents({'year': year, 'month': month}),
        'lis_raw': await lis_raw_col.count_documents({'period': period}),
        'pemakaian': await pemakaian_col.count_documents({'date': {'$regex': f'^{period}'}}),
        'prf': await prf_col.count_documents({'period': period}),
        'penerimaan': await penerimaan_col.count_documents({'period': period}),
    }


@api.delete('/monitoring/periode')
async def hapus_periode(year: int, month: int, hapus_lis: bool = False):
    """Hapus periode (saldo awal / QC / override per reagen). Opsional ikut hapus data LIS bulan itu."""
    if month < 1 or month > 12:
        raise HTTPException(400, 'Bulan tidak valid')
    period = f'{year}-{month:02d}'
    res = await stock_period_col.delete_many({'year': year, 'month': month})
    deleted = {'stock_period': res.deleted_count, 'lis_raw': 0, 'pemakaian': 0}
    if hapus_lis:
        deleted['lis_raw'] = (await lis_raw_col.delete_many({'period': period})).deleted_count
        deleted['pemakaian'] = (await pemakaian_col.delete_many(
            {'date': {'$regex': f'^{period}'}})).deleted_count
    return {'ok': True, 'label': f'{MONTH_NAMES_ID[month]} {year}', 'deleted': deleted}


@api.get('/monitoring/export')
async def export_monitoring(year: int, month: int):
    """Ekspor tabel Pemantauan Stok ke Excel (.xlsx) dengan kolom harian & warna status."""
    if month < 1 or month > 12:
        raise HTTPException(400, 'Bulan tidak valid')
    data = await _compute_monitoring(year, month)
    content = build_workbook(data)
    fname = f'Pemantauan_Stok_{MONTH_NAMES_ID[month]}_{year}.xlsx'
    return Response(
        content=content,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{fname}"'})


# ---------- Notifikasi WhatsApp ----------
@api.get('/notifikasi/whatsapp/preview')
async def wa_preview(year: int, month: int):
    """Pratinjau pesan WhatsApp daftar Kritis & Waspada + status konfigurasi."""
    data = await _compute_monitoring(year, month)
    body, n_crit, n_warn = wa.build_message(data['label'], data['rows'])
    cfg = wa.config()
    last = await import_log_col.find_one({'type': 'whatsapp'}, {'_id': 0}, sort=[('created_at', -1)])
    return {
        'message': body, 'critical': n_crit, 'warning': n_warn,
        'configured': wa.is_configured(), 'recipient': cfg['recipient'] or None,
        'wa_me': wa.wa_me_link(body, cfg['recipient'] or '6285876806380'),
        'last_sent': last,
    }


@api.post('/notifikasi/whatsapp')
async def wa_send(payload: AutoSaldoBody):
    """Kirim daftar Kritis & Waspada ke WhatsApp via Meta Cloud API."""
    if not wa.is_configured():
        raise HTTPException(400, 'WhatsApp belum dikonfigurasi. Isi WHATSAPP_ACCESS_TOKEN & '
                                 'WHATSAPP_PHONE_NUMBER_ID di backend/.env')
    data = await _compute_monitoring(payload.year, payload.month)
    body, n_crit, n_warn = wa.build_message(data['label'], data['rows'])
    ok, info = await wa.send_text(body)
    await import_log_col.insert_one({
        'id': str(uuid.uuid4()), 'type': 'whatsapp', 'period': f'{payload.year}-{payload.month:02d}',
        'recipient': wa.config()['recipient'], 'ok': ok, 'critical': n_crit, 'warning': n_warn,
        'info': info, 'created_at': datetime.now(timezone.utc).isoformat(),
    })
    if not ok:
        raise HTTPException(502, f'WhatsApp API gagal: {info.get("error")}')
    return {'ok': True, 'critical': n_crit, 'warning': n_warn, **info}


# ---------- Mapping & LIS (read-only in phase 1) ----------
class MappingUpdate(BaseModel):
    reagen_name: Optional[str] = None
    status: Optional[str] = None


@api.get('/mapping-tests')
async def mapping_tests(status: Optional[str] = None):
    filt = {}
    if status:
        filt['status'] = status
    docs = await mapping_col.find(filt, {'_id': 0}).to_list(5000)
    total = await mapping_col.count_documents({})
    ok = await mapping_col.count_documents({'status': 'OK'})
    return {'total': total, 'ok': ok, 'tidak_ada': total - ok, 'items': docs}


@api.put('/mapping-tests/{mapping_id}')
async def update_mapping(mapping_id: str, payload: MappingUpdate):
    updates = {}
    if payload.reagen_name is not None:
        updates['reagen_name'] = payload.reagen_name or None
    if payload.status is not None:
        updates['status'] = payload.status
    if not updates:
        raise HTTPException(400, 'Tidak ada perubahan')
    old = await mapping_col.find_one({'id': mapping_id}, {'_id': 0})
    if not old:
        raise HTTPException(404, 'Pemetaan tidak ditemukan')

    new_name = (updates.get('reagen_name') or '').strip() or None
    sync = None
    if 'reagen_name' in updates and new_name:
        updates['reagen_name'] = new_name
        sync = await _sync_master_reagen(old.get('reagen_name'), new_name)
        updates['status'] = 'OK'
    elif 'reagen_name' in updates and not new_name:
        updates['status'] = 'TIDAK ADA'

    await mapping_col.update_one({'id': mapping_id}, {'$set': updates})
    doc = await mapping_col.find_one({'id': mapping_id}, {'_id': 0})
    if sync:
        doc['sync'] = sync
    return doc


async def _sync_master_reagen(old_name, new_name):
    """Ikuti nama reagen monitoring di Pemetaan Test ke Master Reagen.

    - Nama baru sudah ada di master  -> cukup ditautkan.
    - Nama lama ada di master & tidak dipakai pemetaan lain -> master di-rename
      (riwayat stok/periode ikut karena terikat reagen_id).
    - Selain itu -> buat master reagen baru (salin atribut dari reagen lama bila ada).
    """
    if old_name and old_name.strip().lower() == new_name.lower():
        return None
    exists = await reagen_col.find_one({'nama_reagen': re.compile(f'^{re.escape(new_name)}$', re.I)},
                                       {'_id': 0})
    if exists:
        return {'action': 'linked', 'nama_reagen': exists['nama_reagen']}
    old_doc = await reagen_col.find_one({'nama_reagen': old_name}, {'_id': 0}) if old_name else None
    if old_doc:
        others = await mapping_col.count_documents(
            {'reagen_name': old_name, 'status': 'OK'})
        if others <= 1:
            await reagen_col.update_one({'id': old_doc['id']},
                                        {'$set': {'nama_reagen': new_name}})
            await mapping_col.update_many({'reagen_name': old_name},
                                          {'$set': {'reagen_name': new_name}})
            return {'action': 'renamed', 'from': old_name, 'nama_reagen': new_name}
    new_doc = {
        'id': str(uuid.uuid4()),
        'nama_reagen': new_name,
        'item_code': None,
        'qty_per_kit': (old_doc or {}).get('qty_per_kit'),
        'avg_2022': (old_doc or {}).get('avg_2022'),
        'avg_2023': (old_doc or {}).get('avg_2023'),
        'buffer_stock': (old_doc or {}).get('buffer_stock'),
        'satuan': (old_doc or {}).get('satuan', 'Pcs'),
        'aktif': True,
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
    await reagen_col.insert_one(new_doc)
    return {'action': 'created', 'nama_reagen': new_name}


@api.get('/lis/raw')
async def lis_raw(period: Optional[str] = None, limit: int = 500, skip: int = 0):
    filt = {}
    if period:
        filt['period'] = period
    total = await lis_raw_col.count_documents(filt)
    docs = await lis_raw_col.find(filt, {'_id': 0}).skip(skip).limit(limit).to_list(limit)
    all_periods = await lis_raw_col.find({}, {'_id': 0, 'period': 1}).to_list(20000)
    periods_list = sorted({d['period'] for d in all_periods})
    return {'total': total, 'periods': periods_list, 'items': docs}


@api.post('/lis/import')
async def lis_import(files: list[UploadFile] = File(...)):
    """Import satu atau banyak file Excel LIS (nama file LIS_YYMMDD).

    Otomatis mengisi pemakaian harian reagen via Mapping_Test dan
    memperbarui Sisa Stok pada Pemantauan Stok.
    """
    if not files:
        raise HTTPException(400, 'Tidak ada file diunggah')
    payload = []
    for f in files:
        name = f.filename or 'file.xlsx'
        if not name.lower().endswith(('.xlsx', '.xlsm', '.xls')):
            raise HTTPException(400, f'{name}: hanya file Excel (.xlsx / .xls) yang didukung')
        content = await f.read()
        payload.append((name, content))
    summary = await lis_import_files(
        payload, reagen_col, mapping_col, pemakaian_col, lis_raw_col, import_log_col)
    return summary


@api.get('/lis/source-files')
async def lis_source_files(period: Optional[str] = None):
    """Daftar source file LIS (untuk pengelolaan/hapus)."""
    filt = {}
    if period:
        filt['period'] = period
    pipeline = [
        {'$match': filt},
        {'$group': {'_id': '$source_file', 'tests': {'$sum': 1},
                    'period': {'$first': '$period'}}},
        {'$sort': {'_id': 1}},
    ]
    docs = await lis_raw_col.aggregate(pipeline).to_list(5000)
    return [{'source_file': d['_id'], 'tests': d['tests'], 'period': d.get('period')}
            for d in docs if d['_id']]


@api.delete('/lis/source-file/{source_file}')
async def delete_lis_source_file(source_file: str):
    """Hapus semua data LIS mentah & pemakaian harian dari satu source file."""
    raw_res = await lis_raw_col.delete_many({'source_file': source_file})
    pem_res = await pemakaian_col.delete_many({'source_file': source_file})
    if raw_res.deleted_count == 0 and pem_res.deleted_count == 0:
        raise HTTPException(404, 'Source file tidak ditemukan')
    return {'ok': True, 'lis_raw_dihapus': raw_res.deleted_count,
            'pemakaian_dihapus': pem_res.deleted_count}


# ---------- PRF & Penerimaan ----------
class PRFCreate(BaseModel):
    reagen_id: str
    reagent_no: int = 1
    kits: float = 1
    tanggal_pr: str  # YYYY-MM-DD
    note: Optional[str] = None


class PRFReceive(BaseModel):
    tanggal_terima: str  # YYYY-MM-DD
    kits: Optional[float] = None  # override kits actually received


@api.get('/prf')
async def list_prf(period: Optional[str] = None):
    filt = {}
    if period:
        filt['period'] = period
    docs = await prf_col.find(filt, {'_id': 0}).sort('tanggal_pr', 1).to_list(5000)
    mapped = await _mapped_reagen_ids()
    docs = [d for d in docs if d.get('reagen_id') in mapped]
    return {'total': len(docs), 'items': docs}


@api.post('/prf')
async def create_prf(payload: PRFCreate):
    import uuid
    reagen = await reagen_col.find_one({'id': payload.reagen_id}, {'_id': 0})
    if not reagen:
        raise HTTPException(404, 'Reagen tidak ditemukan')
    if len(payload.tanggal_pr) < 7:
        raise HTTPException(400, 'Tanggal PR tidak valid')
    doc = {
        'id': str(uuid.uuid4()),
        'reagen_id': payload.reagen_id,
        'reagen_name': reagen['nama_reagen'],
        'period': payload.tanggal_pr[:7],
        'tanggal_pr': payload.tanggal_pr,
        'reagent_no': payload.reagent_no,
        'kits': payload.kits,
        'status': 'open',
        'tanggal_terima': None,
        'penerimaan_id': None,
        'note': payload.note,
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
    await prf_col.insert_one(doc)
    doc.pop('_id', None)
    return doc


@api.post('/prf/{prf_id}/terima')
async def receive_prf(prf_id: str, payload: PRFReceive):
    """Tandai PRF diterima -> otomatis membuat catatan Penerimaan (berkesinambungan)."""
    import uuid
    prf = await prf_col.find_one({'id': prf_id})
    if not prf:
        raise HTTPException(404, 'PRF tidak ditemukan')
    if prf.get('status') == 'received':
        raise HTTPException(400, 'PRF sudah diterima')
    if len(payload.tanggal_terima) < 7:
        raise HTTPException(400, 'Tanggal terima tidak valid')
    reagen = await reagen_col.find_one({'id': prf['reagen_id']}, {'_id': 0})
    qpk = (reagen or {}).get('qty_per_kit') or 0
    kits = payload.kits if payload.kits is not None else prf.get('kits', 1)
    pen_id = str(uuid.uuid4())
    pen_doc = {
        'id': pen_id,
        'reagen_id': prf['reagen_id'],
        'reagen_name': prf['reagen_name'],
        'period': payload.tanggal_terima[:7],
        'tanggal_terima': payload.tanggal_terima,
        'reagent_no': prf.get('reagent_no'),
        'kits': kits,
        'qty': qpk * kits,
        'prf_id': prf_id,
        'source': 'PRF',
        'note': prf.get('note'),
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
    await penerimaan_col.insert_one(pen_doc)
    await prf_col.update_one({'id': prf_id}, {'$set': {
        'status': 'received',
        'tanggal_terima': payload.tanggal_terima,
        'penerimaan_id': pen_id,
    }})
    pen_doc.pop('_id', None)
    return {'ok': True, 'penerimaan': pen_doc}


@api.delete('/prf/{prf_id}')
async def delete_prf(prf_id: str):
    prf = await prf_col.find_one({'id': prf_id})
    if not prf:
        raise HTTPException(404, 'PRF tidak ditemukan')
    # remove linked penerimaan if any
    if prf.get('penerimaan_id'):
        await penerimaan_col.delete_one({'id': prf['penerimaan_id']})
    await prf_col.delete_one({'id': prf_id})
    return {'ok': True}


@api.get('/penerimaan')
async def list_penerimaan(period: Optional[str] = None):
    filt = {}
    if period:
        filt['period'] = period
    docs = await penerimaan_col.find(filt, {'_id': 0}).sort('tanggal_terima', 1).to_list(5000)
    mapped = await _mapped_reagen_ids()
    docs = [d for d in docs if d.get('reagen_id') in mapped]
    total_qty = sum((d.get('qty') or 0) for d in docs)
    return {'total': len(docs), 'total_qty': total_qty, 'items': docs}


# ---------- Import log ----------
@api.get('/import-log')
async def import_log():
    docs = await import_log_col.find({}, {'_id': 0}).sort('created_at', -1).to_list(100)
    return docs


app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
async def startup():
    try:
        res = await run_seed(force=False)
        logger.info(f'Seed result: {res}')
    except Exception as e:  # pragma: no cover
        logger.exception(f'Seeding failed: {e}')

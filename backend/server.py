"""LabStock backend – Sistem Pemantauan Stok Reagen Laboratorium PK."""
import os
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict
from starlette.middleware.cors import CORSMiddleware

from database import (
    reagen_col, stock_period_col, pemakaian_col, penerimaan_col,
    prf_col, mapping_col, lis_raw_col, import_log_col,
)
from calculations import build_row, days_in_month, STATUS_LABEL
from excel_analysis import EXCEL_SUMMARY
from seeder import run_seed, is_seeded

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
@api.get('/monitoring')
async def monitoring(year: int, month: int):
    if month < 1 or month > 12:
        raise HTTPException(400, 'Bulan tidak valid')

    reagens = await reagen_col.find({}, {'_id': 0}).sort('nama_reagen', 1).to_list(3000)

    periods_docs = await stock_period_col.find(
        {'year': year, 'month': month}, {'_id': 0}).to_list(3000)
    period_by_reagen = {p['reagen_id']: p for p in periods_docs}

    prefix = f'{year}-{month:02d}-'
    pem_docs = await pemakaian_col.find(
        {'date': {'$regex': f'^{prefix}'}}, {'_id': 0}).to_list(50000)
    daily_by_reagen = {}
    for d in pem_docs:
        try:
            day = int(d['date'][8:10])
        except (ValueError, KeyError):
            continue
        daily_by_reagen.setdefault(d['reagen_id'], {})
        daily_by_reagen[d['reagen_id']][day] = daily_by_reagen[d['reagen_id']].get(day, 0) + (d.get('jumlah') or 0)

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


# ---------- Mapping & LIS (read-only in phase 1) ----------
@api.get('/mapping-tests')
async def mapping_tests(status: Optional[str] = None):
    filt = {}
    if status:
        filt['status'] = status
    docs = await mapping_col.find(filt, {'_id': 0}).to_list(5000)
    total = await mapping_col.count_documents({})
    ok = await mapping_col.count_documents({'status': 'OK'})
    return {'total': total, 'ok': ok, 'tidak_ada': total - ok, 'items': docs}


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


# ---------- PRF & Penerimaan ----------
@api.get('/prf')
async def list_prf(period: Optional[str] = None):
    filt = {}
    if period:
        filt['period'] = period
    docs = await prf_col.find(filt, {'_id': 0}).sort('tanggal_pr', 1).to_list(5000)
    return {'total': len(docs), 'items': docs}


@api.get('/penerimaan')
async def list_penerimaan(period: Optional[str] = None):
    filt = {}
    if period:
        filt['period'] = period
    docs = await penerimaan_col.find(filt, {'_id': 0}).sort('tanggal_terima', 1).to_list(5000)
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

"""Persistensi perubahan Pemetaan Test & Master Reagen ke seed/seed_data.json.

Tujuan: perubahan yang dibuat pengguna (rename reagen monitoring, tambah pemetaan
baru, reagen baru) tetap ada walaupun database di-seed ulang (reseed / DB reset).
Penulisan file dilakukan atomik (tulis ke .tmp lalu replace).
"""
import json
import asyncio
import logging
from pathlib import Path

logger = logging.getLogger('labstock.seed_store')

SEED_FILE = Path(__file__).parent / 'seed' / 'seed_data.json'
_lock = asyncio.Lock()

# Sheet yang memakai kolom 'reagen' sebagai nama reagen monitoring
REAGEN_SHEETS = ('Juli2026', 'Aug2026', 'PRF', 'Penerimaan')
# Sheet pemakaian harian lama memakai kolom 'test'
PQ_SHEETS = ('PQ_Juli', 'PQ_Aug')


def _load():
    return json.loads(SEED_FILE.read_text())


def _save(data):
    tmp = SEED_FILE.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    tmp.replace(SEED_FILE)


def _norm(s):
    return (s or '').strip().lower()


async def persist_mapping(lis_name, reagen_name, status):
    """Simpan/update satu baris Mapping_Test (kunci: lis_name, case-insensitive)."""
    if not lis_name:
        return
    async with _lock:
        try:
            data = _load()
            items = data.setdefault('Mapping_Test', [])
            key = _norm(lis_name)
            for m in items:
                if _norm(m.get('lis_name')) == key:
                    m['reagen'] = reagen_name
                    m['status'] = status
                    break
            else:
                items.append({'lis_name': lis_name, 'reagen': reagen_name, 'status': status})
            _save(data)
        except Exception as e:  # jangan sampai gagal simpan seed mematikan request
            logger.exception(f'persist_mapping gagal: {e}')


async def remove_mapping(lis_name):
    """Hapus satu baris Mapping_Test dari seed_data.json (kunci: lis_name, case-insensitive)."""
    if not lis_name:
        return
    async with _lock:
        try:
            data = _load()
            items = data.get('Mapping_Test', [])
            key = _norm(lis_name)
            data['Mapping_Test'] = [m for m in items if _norm(m.get('lis_name')) != key]
            _save(data)
        except Exception as e:
            logger.exception(f'remove_mapping gagal: {e}')


async def persist_reagen_rename(old_name, new_name):
    """Ganti nama reagen di semua sheet seed (master, PRF, penerimaan, PQ, mapping, extra)."""
    if not old_name or not new_name or _norm(old_name) == _norm(new_name):
        return
    async with _lock:
        try:
            data = _load()
            key = _norm(old_name)
            for sheet in REAGEN_SHEETS:
                for row in data.get(sheet, []):
                    if _norm(row.get('reagen')) == key:
                        row['reagen'] = new_name
            for sheet in PQ_SHEETS:
                for row in data.get(sheet, []):
                    if _norm(row.get('test')) == key:
                        row['test'] = new_name
            for m in data.get('Mapping_Test', []):
                if _norm(m.get('reagen')) == key:
                    m['reagen'] = new_name
            for r in data.get('Master_Extra', []):
                if _norm(r.get('nama_reagen')) == key:
                    r['nama_reagen'] = new_name
            _save(data)
        except Exception as e:
            logger.exception(f'persist_reagen_rename gagal: {e}')


async def persist_new_reagen(doc):
    """Tambahkan reagen baru ke daftar Master_Extra (dibaca seeder saat seed ulang)."""
    if not doc or not doc.get('nama_reagen'):
        return
    async with _lock:
        try:
            data = _load()
            extra = data.setdefault('Master_Extra', [])
            key = _norm(doc['nama_reagen'])
            rec = {
                'nama_reagen': doc['nama_reagen'],
                'item_code': doc.get('item_code'),
                'qty_per_kit': doc.get('qty_per_kit'),
                'avg_2022': doc.get('avg_2022'),
                'avg_2023': doc.get('avg_2023'),
                'buffer_stock': doc.get('buffer_stock'),
                'satuan': doc.get('satuan') or 'Pcs',
            }
            for i, r in enumerate(extra):
                if _norm(r.get('nama_reagen')) == key:
                    extra[i] = rec
                    break
            else:
                extra.append(rec)
            _save(data)
        except Exception as e:
            logger.exception(f'persist_new_reagen gagal: {e}')

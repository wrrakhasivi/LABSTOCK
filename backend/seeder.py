"""Seed MongoDB from the analyzed Excel data (seed/seed_data.json).

Date-based: daily usage stored per (reagen_id, date, jumlah); NOT 31 columns.
"""
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

from database import (
    reagen_col, stock_period_col, pemakaian_col, penerimaan_col,
    prf_col, mapping_col, lis_raw_col, import_log_col, ensure_indexes,
)
from calculations import to_number

SEED_FILE = Path(__file__).parent / 'seed' / 'seed_data.json'

PERIODS = {
    'Juli2026': (2026, 7),
    'Aug2026': (2026, 8),
}
PQ_PERIOD = {'PQ_Juli': (2026, 7), 'PQ_Aug': (2026, 8)}


def _parse_date(s):
    """Parse '2026-07-07 00:00:00' or '2026-07-07' -> 'YYYY-MM-DD'."""
    if not s:
        return None
    s = str(s).strip()
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S'):
        try:
            return datetime.strptime(s, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None


async def is_seeded():
    return (await reagen_col.count_documents({})) > 0


async def run_seed(force=False):
    await ensure_indexes()
    if await is_seeded() and not force:
        return {'seeded': False, 'reason': 'already seeded'}

    # Clear collections
    for col in (reagen_col, stock_period_col, pemakaian_col, penerimaan_col,
                prf_col, mapping_col, lis_raw_col):
        await col.delete_many({})

    data = json.loads(SEED_FILE.read_text())

    # 1) Build master_reagen from union of monthly sheets (prefer later month values)
    name_to_id = {}
    master = {}
    for sheet in ('Juli2026', 'Aug2026'):
        for row in data.get(sheet, []):
            name = row['reagen']
            rec = master.get(name, {})
            def pick(field, key):
                v = to_number(row.get(key)) if key in ('qty_per_kit', 'avg_2022', 'avg_2023', 'buffer_stock') else row.get(key)
                if v is not None and v != '':
                    rec[field] = v
            pick('qty_per_kit', 'qty_per_kit')
            pick('avg_2022', 'avg_2022')
            pick('avg_2023', 'avg_2023')
            pick('buffer_stock', 'buffer_stock')
            if row.get('satuan'):
                rec['satuan'] = row['satuan']
            master[name] = rec

    reagen_docs = []
    for name, rec in master.items():
        rid = str(uuid.uuid4())
        name_to_id[name] = rid
        reagen_docs.append({
            'id': rid,
            'nama_reagen': name,
            'item_code': None,
            'qty_per_kit': rec.get('qty_per_kit'),
            'avg_2022': rec.get('avg_2022'),
            'avg_2023': rec.get('avg_2023'),
            'buffer_stock': rec.get('buffer_stock'),
            'satuan': rec.get('satuan') or 'Pcs',
            'aktif': True,
            'created_at': datetime.now(timezone.utc).isoformat(),
        })

    async def ensure_reagen(name):
        """Return reagen id, creating a stub if the name is new."""
        if name in name_to_id:
            return name_to_id[name]
        rid = str(uuid.uuid4())
        name_to_id[name] = rid
        doc = {
            'id': rid, 'nama_reagen': name, 'item_code': None,
            'qty_per_kit': None, 'avg_2022': None, 'avg_2023': None,
            'buffer_stock': None, 'satuan': 'Pcs', 'aktif': True,
            'created_at': datetime.now(timezone.utc).isoformat(),
        }
        reagen_docs.append(doc)
        return rid

    # 2) stock_period per (reagen, month)
    period_docs = []
    for sheet, (yr, mo) in PERIODS.items():
        for row in data.get(sheet, []):
            rid = await ensure_reagen(row['reagen'])
            period_docs.append({
                'id': str(uuid.uuid4()),
                'reagen_id': rid,
                'year': yr,
                'month': mo,
                'saldo_awal': to_number(row.get('saldo_awal')),
                'qc': to_number(row.get('qc')) or 0,
                'buffer_override': None,
                'created_at': datetime.now(timezone.utc).isoformat(),
            })

    # 3) pemakaian_harian from PQ sheets (date-based)
    pemakaian_docs = []
    for sheet, (yr, mo) in PQ_PERIOD.items():
        for row in data.get(sheet, []):
            rid = await ensure_reagen(row['test'])
            for day_str, jumlah in row.get('days', {}).items():
                try:
                    day = int(day_str)
                except ValueError:
                    continue
                date = f"{yr}-{mo:02d}-{day:02d}"
                pemakaian_docs.append({
                    'id': str(uuid.uuid4()),
                    'reagen_id': rid,
                    'date': date,
                    'jumlah': to_number(jumlah) or 0,
                    'source': 'PQ',
                })

    # 4) mapping_test
    mapping_docs = []
    for m in data.get('Mapping_Test', []):
        mapping_docs.append({
            'id': str(uuid.uuid4()),
            'lis_name': m.get('lis_name'),
            'reagen_name': m.get('reagen'),
            'status': m.get('status'),
        })

    # 5) lis_raw (date-based rows expanded from days)
    lis_docs = []
    for sheet in ('LIS_Juli', 'LIS_Aug'):
        for row in data.get(sheet, []):
            period = row.get('period')
            yr, mo = int(period[:4]), int(period[5:7])
            lis_docs.append({
                'id': str(uuid.uuid4()),
                'period': period,
                'grup': row.get('grup'),
                'nama_test': row.get('nama_test'),
                'total': to_number(row.get('total')),
                'source_file': row.get('source_file'),
                'days': row.get('days', {}),
            })

    # 6) PRF
    prf_docs = []
    for p in data.get('PRF', []):
        rid = await ensure_reagen(p['reagen'])
        prf_docs.append({
            'id': str(uuid.uuid4()),
            'reagen_id': rid,
            'reagen_name': p['reagen'],
            'period': p.get('period'),
            'tanggal_pr': _parse_date(p.get('tanggal_pr')),
            'reagent_no': p.get('reagent_no'),
            'kits': to_number(p.get('kits')) or 1,
            'status': 'open',
            'note': None,
        })

    # 7) penerimaan
    pen_docs = []
    for p in data.get('Penerimaan', []):
        rid = await ensure_reagen(p['reagen'])
        qpk = to_number(p.get('qty_per_kit')) or 0
        kits = to_number(p.get('kits')) or 1
        pen_docs.append({
            'id': str(uuid.uuid4()),
            'reagen_id': rid,
            'reagen_name': p['reagen'],
            'period': p.get('period'),
            'tanggal_terima': _parse_date(p.get('tanggal_terima')),
            'reagent_no': p.get('reagent_no'),
            'kits': kits,
            'qty': qpk * kits,
            'note': None,
        })

    # Insert all
    if reagen_docs:
        await reagen_col.insert_many(reagen_docs)
    if period_docs:
        await stock_period_col.insert_many(period_docs)
    if pemakaian_docs:
        await pemakaian_col.insert_many(pemakaian_docs)
    if mapping_docs:
        await mapping_col.insert_many(mapping_docs)
    if lis_docs:
        await lis_raw_col.insert_many(lis_docs)
    if prf_docs:
        await prf_col.insert_many(prf_docs)
    if pen_docs:
        await penerimaan_col.insert_many(pen_docs)

    summary = {
        'reagen': len(reagen_docs),
        'stock_period': len(period_docs),
        'pemakaian_harian': len(pemakaian_docs),
        'mapping_test': len(mapping_docs),
        'lis_raw': len(lis_docs),
        'prf': len(prf_docs),
        'penerimaan': len(pen_docs),
    }
    await import_log_col.insert_one({
        'id': str(uuid.uuid4()),
        'type': 'seed',
        'filename': 'seed_data.json',
        'period': '2026-07,2026-08',
        'inserted': summary,
        'errors': [],
        'created_at': datetime.now(timezone.utc).isoformat(),
    })
    return {'seeded': True, 'summary': summary}

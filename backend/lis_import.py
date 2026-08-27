"""Parse & import LIS Excel exports into pemakaian_harian (date-based).

Filename convention: LIS_YYMMDD  (mis. LIS_260802 = 2 Agustus 2026).
Also supports LIS_YYMM (satu bulan) + kolom tanggal/hari di dalam file.

Kolom yang didukung di dalam file Excel:
  - "Nama Test" (wajib), "Grup" (opsional)
  - "Jumlah"/"Total"/"Qty"  -> nilai untuk 1 tanggal (dari nama file), ATAU
  - beberapa kolom tanggal/hari (header angka 1..31 atau tanggal) -> multi-hari.

Test LIS dipetakan ke reagen lewat Mapping_Test (status OK). 1 test = 1 pemakaian.
"""
import re
import io
import uuid
from datetime import datetime, date, timezone

import openpyxl

from calculations import to_number

FNAME_DATE = re.compile(r'(\d{2})(\d{2})(\d{2})')   # YYMMDD
FNAME_MONTH = re.compile(r'(\d{2})(\d{2})(?!\d)')    # YYMM


def _parse_filename(name):
    """Return (year, month, day|None) from a LIS_YYMMDD / LIS_YYMM filename."""
    stem = name.rsplit('.', 1)[0]
    core = stem.upper().replace('LIS', '').strip('_ -')
    m = FNAME_DATE.search(core)
    if m:
        yy, mm, dd = (int(x) for x in m.groups())
        if 1 <= mm <= 12 and 1 <= dd <= 31:
            return 2000 + yy, mm, dd
    m = FNAME_MONTH.search(core)
    if m:
        yy, mm = int(m.group(1)), int(m.group(2))
        if 1 <= mm <= 12:
            return 2000 + yy, mm, None
    return None, None, None


def _norm(v):
    return str(v).strip().lower() if v is not None else ''


def _resolve_col_date(header, base_year, base_month):
    """Turn a day-column header into 'YYYY-MM-DD' if possible."""
    if isinstance(header, (datetime, date)):
        return f'{header.year}-{header.month:02d}-{header.day:02d}'
    n = to_number(header)
    if n is not None and base_year and base_month:
        d = int(n)
        if 1 <= d <= 31:
            return f'{base_year}-{base_month:02d}-{d:02d}'
    return None


def parse_file(filename, content):
    """Parse a single Excel file. Returns (per_date_test, warnings).

    per_date_test: { 'YYYY-MM-DD': { test_name: jumlah } }
    """
    year, month, day = _parse_filename(filename)
    warnings = []
    wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return {}, ['File kosong']

    # Find header row (contains a "nama test"/"test" cell)
    header_idx, cols = None, {}
    for i, row in enumerate(rows[:15]):
        lowered = [_norm(c) for c in row]
        test_col = None
        for j, c in enumerate(lowered):
            if c in ('nama test', 'test', 'nama tes', 'tes', 'pemeriksaan', 'nama pemeriksaan'):
                test_col = j
                break
        if test_col is not None:
            header_idx = i
            cols['test'] = test_col
            for j, c in enumerate(lowered):
                if c in ('grup', 'group', 'kelompok'):
                    cols['grup'] = j
                elif c in ('jumlah', 'total', 'qty', 'quantity', 'jml'):
                    cols['jumlah'] = j
            # date/day columns = remaining columns with numeric/date headers
            date_cols = {}
            for j, raw in enumerate(row):
                if j in (cols.get('test'), cols.get('grup'), cols.get('jumlah')):
                    continue
                resolved = _resolve_col_date(raw, year, month)
                if resolved:
                    date_cols[j] = resolved
            cols['date_cols'] = date_cols
            break

    if header_idx is None:
        return {}, [f'{filename}: header "Nama Test" tidak ditemukan']

    per_date = {}

    def add(d, test, jumlah):
        if not d or not test:
            return
        j = to_number(jumlah)
        if not j:
            return
        per_date.setdefault(d, {})
        per_date[d][test] = per_date[d].get(test, 0) + j

    use_date_cols = bool(cols.get('date_cols'))
    base_date = f'{year}-{month:02d}-{day:02d}' if (year and month and day) else None

    if not use_date_cols and base_date is None:
        return {}, [f'{filename}: tanggal tidak diketahui (gunakan nama file LIS_YYMMDD atau kolom tanggal)']

    for row in rows[header_idx + 1:]:
        if row is None:
            continue
        test = row[cols['test']] if cols['test'] < len(row) else None
        test = str(test).strip() if test is not None else ''
        if not test or _norm(test) in ('total', 'grand total', 'jumlah', 'nama test'):
            continue
        if use_date_cols:
            for j, d in cols['date_cols'].items():
                if j < len(row):
                    add(d, test, row[j])
        else:
            jcol = cols.get('jumlah')
            val = row[jcol] if (jcol is not None and jcol < len(row)) else None
            if val is None:
                # fallback: first numeric cell after test col
                for k in range(cols['test'] + 1, len(row)):
                    if to_number(row[k]) is not None:
                        val = row[k]
                        break
            add(base_date, test, val)

    if not per_date:
        warnings.append(f'{filename}: tidak ada data pemakaian terbaca')
    return per_date, warnings


async def import_files(files, reagen_col, mapping_col, pemakaian_col, lis_raw_col, import_log_col):
    """files: list of (filename, bytes). Returns summary dict."""
    # Build lookup maps
    reagens = await reagen_col.find({}, {'_id': 0, 'id': 1, 'nama_reagen': 1}).to_list(5000)
    master_map = {r['nama_reagen'].strip().lower(): r['id'] for r in reagens}
    mappings = await mapping_col.find({'status': 'OK'}, {'_id': 0}).to_list(5000)
    map_lis = {}
    for m in mappings:
        if m.get('lis_name') and m.get('reagen_name'):
            map_lis[m['lis_name'].strip().lower()] = m['reagen_name'].strip()

    file_reports = []
    all_dates = set()
    # (reagen_id, date) -> jumlah
    pem_acc = {}
    unmatched_global = {}
    lis_raw_new = []

    for filename, content in files:
        try:
            per_date, warnings = parse_file(filename, content)
        except Exception as e:  # noqa
            file_reports.append({'filename': filename, 'error': str(e), 'dates': [], 'tests': 0,
                                 'matched': 0, 'unmatched': []})
            continue

        year, month, _ = _parse_filename(filename)
        stem = filename.rsplit('.', 1)[0]
        file_unmatched = set()
        file_test_days = {}  # test -> {day: jumlah}
        matched = 0
        tests = set()
        for d, tests_map in per_date.items():
            all_dates.add(d)
            day = int(d[8:10])
            for test, jumlah in tests_map.items():
                tests.add(test)
                key = test.strip().lower()
                reagen_name = map_lis.get(key)
                if not reagen_name and key in master_map:
                    reagen_name = test.strip()
                reagen_id = master_map.get((reagen_name or '').strip().lower()) if reagen_name else None
                if reagen_id:
                    pem_acc[(reagen_id, d, stem)] = pem_acc.get((reagen_id, d, stem), 0) + jumlah
                    matched += 1
                else:
                    file_unmatched.add(test)
                    unmatched_global[test] = unmatched_global.get(test, 0) + 1
                # raw
                file_test_days.setdefault(test, {})
                file_test_days[test][str(day)] = file_test_days[test].get(str(day), 0) + jumlah

        # build lis_raw rows for this file
        period = f'{year}-{month:02d}' if (year and month) else (sorted(all_dates)[0][:7] if all_dates else None)
        for test, days in file_test_days.items():
            lis_raw_new.append({
                'id': str(uuid.uuid4()),
                'period': period,
                'grup': None,
                'nama_test': test,
                'total': sum(days.values()),
                'source_file': stem,
                'days': days,
            })

        file_reports.append({
            'filename': filename,
            'dates': sorted(per_date.keys()),
            'tests': len(tests),
            'matched': matched,
            'unmatched': sorted(file_unmatched),
            'warnings': warnings,
        })

    # Idempotent: replace pemakaian for affected dates, and lis_raw for affected source files
    if all_dates:
        await pemakaian_col.delete_many({'date': {'$in': list(all_dates)}})
    source_files = [f[0].rsplit('.', 1)[0] for f in files]
    if source_files:
        await lis_raw_col.delete_many({'source_file': {'$in': source_files}})

    pem_docs = [{
        'id': str(uuid.uuid4()),
        'reagen_id': rid,
        'date': d,
        'jumlah': jumlah,
        'source': 'LIS',
        'source_file': stem,
    } for (rid, d, stem), jumlah in pem_acc.items()]

    if pem_docs:
        await pemakaian_col.insert_many(pem_docs)
    if lis_raw_new:
        await lis_raw_col.insert_many(lis_raw_new)

    summary = {
        'files': file_reports,
        'dates_affected': sorted(all_dates),
        'pemakaian_records': len(pem_docs),
        'reagen_terdampak': len({rid for (rid, _, _) in pem_acc.keys()}),
        'unmatched_tests': sorted(unmatched_global.keys()),
    }
    await import_log_col.insert_one({
        'id': str(uuid.uuid4()),
        'type': 'lis_import',
        'filename': ', '.join(f[0] for f in files),
        'period': ','.join(sorted({d[:7] for d in all_dates})),
        'inserted': {'pemakaian': len(pem_docs), 'lis_raw': len(lis_raw_new)},
        'errors': summary['unmatched_tests'][:50],
        'created_at': datetime.now(timezone.utc).isoformat(),
    })
    return summary

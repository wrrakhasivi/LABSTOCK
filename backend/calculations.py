"""Business calculation logic mirroring the Excel workbook."""
import calendar

STATUS_SPARE = 10  # spare before buffer that triggers WASPADA (Excel note)


def to_number(v):
    """Convert Excel value to number; #REF!/None/blank -> None."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return v
    s = str(v).strip()
    if s == '' or s.startswith('#'):
        return None
    try:
        if '.' in s:
            return float(s)
        return int(s)
    except ValueError:
        return None


def compute_status(sisa, buffer):
    """Return status code based on Excel conditional formatting rules.

    KRITIS  : sisa <= buffer
    WASPADA : buffer < sisa <= buffer + spare(10)
    AMAN    : sisa > buffer + spare
    unknown : data tidak lengkap
    """
    if sisa is None or buffer is None:
        return 'unknown'
    if sisa <= buffer:
        return 'critical'
    if sisa <= buffer + STATUS_SPARE:
        return 'warning'
    return 'safe'


STATUS_LABEL = {
    'critical': 'KRITIS',
    'warning': 'WASPADA',
    'safe': 'AMAN',
    'unknown': 'PERLU CEK',
}


def days_in_month(year, month):
    return calendar.monthrange(year, month)[1]


def build_row(reagen, period, daily_map, stok_masuk, prf_list, pen_list, year, month):
    """Assemble one monitoring row.

    reagen: master_reagen doc
    period: stock_period doc or None
    daily_map: {day_int: jumlah}
    stok_masuk: total qty masuk (number)
    """
    ndays = days_in_month(year, month)
    hari = {}
    total_harian = 0
    for d in range(1, ndays + 1):
        val = daily_map.get(d, 0) or 0
        hari[str(d)] = val
        total_harian += val

    qc = (period or {}).get('qc') or 0
    saldo_awal = (period or {}).get('saldo_awal')
    saldo_awal = to_number(saldo_awal)
    buffer = to_number(reagen.get('buffer_stock'))

    total_pemakaian = total_harian + (qc or 0)
    stok_masuk = stok_masuk or 0

    sisa = None
    if saldo_awal is not None:
        sisa = (saldo_awal - total_pemakaian) + stok_masuk

    status = compute_status(sisa, buffer)

    return {
        'reagen_id': reagen['id'],
        'nama_reagen': reagen['nama_reagen'],
        'qty_per_kit': reagen.get('qty_per_kit'),
        'satuan': reagen.get('satuan'),
        'hari': hari,
        'qc': qc,
        'total_pemakaian': total_pemakaian,
        'saldo_awal': saldo_awal,
        'stok_masuk': stok_masuk,
        'sisa_stock': sisa,
        'saldo_akhir': sisa,
        'buffer_stock': buffer,
        'status': status,
        'status_label': STATUS_LABEL[status],
        'prf': prf_list,
        'penerimaan': pen_list,
    }

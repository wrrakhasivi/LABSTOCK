import React, { useEffect, useMemo, useRef, useState } from 'react';
import { usePeriod } from '../lib/period';
import { api, fmtNum, MONTHS_ID } from '../lib/api';
import { useAuth } from '../lib/auth';
import { StatusBadge } from '../components/StatusBadge';
import { ExportButton, DeletePeriodButton } from '../components/PeriodActions';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription,
  AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger,
} from '../components/ui/alert-dialog';
import { toast } from 'sonner';
import { Search, RefreshCw, Info, Wand2, Pencil, ArrowUpDown, ArrowUp, ArrowDown, CalendarPlus } from 'lucide-react';

const FILTERS = [
  { key: 'all', label: 'Semua', cls: 'data-[active=true]:bg-primary data-[active=true]:text-primary-foreground' },
  { key: 'critical', label: 'Kritis', cls: 'data-[active=true]:bg-red-600 data-[active=true]:text-white' },
  { key: 'warning', label: 'Waspada', cls: 'data-[active=true]:bg-amber-500 data-[active=true]:text-slate-950' },
  { key: 'safe', label: 'Aman', cls: 'data-[active=true]:bg-emerald-600 data-[active=true]:text-white' },
  { key: 'unknown', label: 'Perlu Cek', cls: 'data-[active=true]:bg-slate-500 data-[active=true]:text-white' },
];

// Inline-editable numeric cell (click to edit; Enter/blur = simpan, Esc = batal, kosong = null)
function EditableNumber({ value, onSave, testid, alignCls = 'text-right', valueCls = '', marker = null, title, editable = true }) {
  const [editing, setEditing] = useState(false);
  const [val, setVal] = useState('');
  const inputRef = useRef(null);

  const start = () => {
    if (!editable) return;
    setVal(value === null || value === undefined ? '' : String(value));
    setEditing(true);
  };
  useEffect(() => { if (editing && inputRef.current) inputRef.current.select(); }, [editing]);

  const commit = () => {
    setEditing(false);
    const trimmed = val.trim();
    const parsed = trimmed === '' ? null : Number(trimmed);
    if (trimmed !== '' && Number.isNaN(parsed)) { toast.error('Nilai harus angka'); return; }
    const current = value === null || value === undefined ? null : Number(value);
    if (parsed === current) return; // no change
    onSave(parsed);
  };

  if (editing) {
    return (
      <td className={`border-b px-1 py-1 ${alignCls}`}>
        <input
          ref={inputRef}
          type="number"
          data-testid={`${testid}-input`}
          className="num h-7 w-16 rounded border border-primary bg-background px-1 text-right text-sm outline-none ring-2 ring-ring"
          value={val}
          onChange={(e) => setVal(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => {
            if (e.key === 'Enter') commit();
            else if (e.key === 'Escape') setEditing(false);
          }}
        />
      </td>
    );
  }

  return (
    <td
      className={`num ${editable ? 'group/edit cursor-pointer hover:bg-primary/5' : ''} border-b px-2 py-1.5 ${alignCls} ${valueCls}`}
      data-testid={testid}
      title={editable ? (title || 'Klik untuk edit') : title}
      onClick={start}
    >
      <span className="inline-flex items-center gap-1">
        {marker}
        {fmtNum(value)}
        {editable && <Pencil className="h-3 w-3 opacity-0 text-muted-foreground transition-opacity group-hover/edit:opacity-70" />}
      </span>
    </td>
  );
}

// Kolom harian editable (untuk reagen turunan seperti Kit Elisa Quantiferon = Quantiferon Tube x4)
function EditableDay({ value, onSave, testid, editable, isOverridden, isToday, day }) {
  const [editing, setEditing] = useState(false);
  const [val, setVal] = useState('');
  const inputRef = useRef(null);

  const start = () => {
    if (!editable) return;
    setVal(value === null || value === undefined ? '' : String(value));
    setEditing(true);
  };
  useEffect(() => { if (editing && inputRef.current) inputRef.current.select(); }, [editing]);

  const commit = () => {
    setEditing(false);
    const trimmed = val.trim();
    const parsed = trimmed === '' ? null : Number(trimmed);
    if (trimmed !== '' && Number.isNaN(parsed)) { toast.error('Nilai harus angka'); return; }
    const current = value === null || value === undefined ? null : Number(value);
    if (parsed === current) return;
    onSave(parsed);
  };

  if (editing) {
    return (
      <td className={`ls-day-col border-b py-1 ${isToday ? 'ls-today' : ''}`}>
        <input
          ref={inputRef}
          type="number"
          data-testid={`${testid}-input`}
          className="num h-6 w-full rounded border border-primary bg-background px-0 text-center text-[11px] outline-none ring-1 ring-ring"
          value={val}
          onChange={(e) => setVal(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => {
            if (e.key === 'Enter') commit();
            else if (e.key === 'Escape') setEditing(false);
          }}
        />
      </td>
    );
  }

  return (
    <td
      className={`ls-day-col border-b py-1.5 ${editable ? 'cursor-pointer hover:bg-primary/10' : ''} ${isOverridden ? 'font-bold text-amber-600' : (value ? '' : 'text-muted-foreground/40')} ${isToday ? 'ls-today' : ''}`}
      data-testid={testid}
      title={isOverridden ? `Hari ${day}: nilai manual (klik untuk edit)` : `Hari ${day}: default otomatis = Quantiferon Tube × 4 (klik untuk edit manual)`}
      onClick={start}
    >
      {value || ''}
    </td>
  );
}

export default function PemantauanStok() {
  const { isKoordinator } = useAuth();
  const { year, month, setYear, setMonth, refreshPeriods } = usePeriod();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');
  const [q, setQ] = useState('');
  const [autoLoading, setAutoLoading] = useState(false);
  const [newPeriodOpen, setNewPeriodOpen] = useState(false);
  const [newPeriodLoading, setNewPeriodLoading] = useState(false);
  const [sortDir, setSortDir] = useState('asc'); // 'asc' | 'desc' | null

  const nextPeriod = month === 12 ? { year: year + 1, month: 1 } : { year, month: month + 1 };
  const nextLabel = `${MONTHS_ID[nextPeriod.month]} ${nextPeriod.year}`;

  const runNewPeriod = async () => {
    setNewPeriodLoading(true);
    try {
      const res = await api.buatPeriodeBaru(year, month);
      toast.success(`Periode ${res.label} dibuat: saldo awal ${res.reagen} reagen diambil dari sisa stok ${res.from_period}`);
      setNewPeriodOpen(false);
      await refreshPeriods();
      setYear(res.year);
      setMonth(res.month);
    } catch (e) {
      toast.error('Gagal membuat periode baru');
    } finally {
      setNewPeriodLoading(false);
    }
  };

  const load = () => {
    setLoading(true);
    setError(null);
    api.monitoring(year, month)
      .then((d) => setData(d))
      .catch(() => setError('Gagal memuat data pemantauan.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [year, month]);

  const days = data?.days || 31;
  const dayCols = useMemo(() => Array.from({ length: days }, (_, i) => i + 1), [days]);
  // Sorot kolom tanggal hari ini (hanya jika periode yang dilihat = bulan & tahun berjalan)
  const now = new Date();
  const shownYear = data?.year ?? year;
  const shownMonth = data?.month ?? month;
  const todayCol = now.getFullYear() === Number(shownYear) && now.getMonth() + 1 === Number(shownMonth) ? now.getDate() : null;

  const rows = useMemo(() => {
    if (!data) return [];
    const list = data.rows.filter((r) => {
      if (filter !== 'all' && r.status !== filter) return false;
      if (q && !r.nama_reagen.toLowerCase().includes(q.toLowerCase())) return false;
      return true;
    });
    if (sortDir) {
      list.sort((a, b) => a.nama_reagen.localeCompare(b.nama_reagen, 'id', { sensitivity: 'base' }));
      if (sortDir === 'desc') list.reverse();
    }
    return list;
  }, [data, filter, q, sortDir]);

  const toggleSort = () => setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
  const SortIcon = sortDir === 'asc' ? ArrowUp : sortDir === 'desc' ? ArrowDown : ArrowUpDown;

  const saveSaldo = async (row, value) => {
    try {
      await api.setSaldoAwal({ reagen_id: row.reagen_id, year, month, saldo_awal: value });
      toast.success(`Saldo awal "${row.nama_reagen}" diperbarui`);
      load();
    } catch (e) { toast.error('Gagal menyimpan saldo awal'); }
  };

  const saveQc = async (row, value) => {
    try {
      await api.setQc({ reagen_id: row.reagen_id, year, month, qc: value });
      toast.success(`QC "${row.nama_reagen}" diperbarui`);
      load();
    } catch (e) { toast.error('Gagal menyimpan QC'); }
  };

  const saveHari = async (row, day, value) => {
    try {
      await api.setHariOverride({ reagen_id: row.reagen_id, year, month, day, value });
      toast.success(`Nilai hari ${day} untuk "${row.nama_reagen}" diperbarui`);
      load();
    } catch (e) { toast.error('Gagal menyimpan nilai harian'); }
  };

  const markedDaysSet = useMemo(() => new Set(data?.marked_days || []), [data]);

  const toggleMark = async (day) => {
    const isMarked = markedDaysSet.has(day);
    try {
      await api.toggleTanggalMark({ year, month, day, marked: !isMarked });
      load();
    } catch (e) { toast.error('Gagal menyimpan tanda tanggal'); }
  };

  const runAuto = async () => {
    setAutoLoading(true);
    try {
      const res = await api.autoSaldoAwal(year, month);
      toast.success(`Saldo awal ${res.updated} reagen diisi dari ${res.from_period}`);
      load();
    } catch (e) {
      toast.error('Gagal mengisi saldo awal otomatis');
    } finally {
      setAutoLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Header + filters */}
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="text-sm text-muted-foreground">Pemantauan pemakaian & stok reagen</div>
          <div className="text-lg font-semibold">{data?.label || `${month}/${year}`}</div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              data-testid="pemantauan-search"
              placeholder="Cari reagen..."
              value={q}
              onChange={(e) => setQ(e.target.value)}
              className="h-9 w-[200px] pl-8"
            />
          </div>
          <Button variant="outline" size="sm" onClick={runAuto} disabled={autoLoading || !isKoordinator} data-testid="auto-saldo-awal-button" title={isKoordinator ? 'Isi Saldo Awal = Sisa Stok bulan sebelumnya' : 'Hanya Koordinator yang dapat mengubah saldo awal'}>
            <Wand2 className="mr-1.5 h-3.5 w-3.5" /> {autoLoading ? 'Memproses...' : 'Saldo Awal Otomatis'}
          </Button>
          <AlertDialog open={newPeriodOpen} onOpenChange={setNewPeriodOpen}>
            <AlertDialogTrigger asChild>
              <Button size="sm" data-testid="new-period-button" title={`Buat periode ${nextLabel}`} disabled={!isKoordinator}>
                <CalendarPlus className="mr-1.5 h-3.5 w-3.5" /> Periode Bulan Baru
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent data-testid="new-period-dialog">
              <AlertDialogHeader>
                <AlertDialogTitle>Buat periode {nextLabel}?</AlertDialogTitle>
                <AlertDialogDescription>
                  Saldo Awal setiap reagen pada <b>{nextLabel}</b> akan diisi dari Sisa Stok <b>{data?.label || `${month}/${year}`}</b> saat ini.
                  Jika periode {nextLabel} sudah ada, saldo awalnya akan ditimpa dengan nilai terbaru.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel data-testid="new-period-cancel">Batal</AlertDialogCancel>
                <AlertDialogAction onClick={(e) => { e.preventDefault(); runNewPeriod(); }} disabled={newPeriodLoading} data-testid="new-period-confirm">
                  {newPeriodLoading ? 'Memproses...' : `Buat ${nextLabel}`}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
          <ExportButton year={year} month={month} />
          {isKoordinator && <DeletePeriodButton year={year} month={month} label={data?.label || `${month}/${year}`} />}
          <Button variant="outline" size="sm" onClick={load} data-testid="pemantauan-reload-button">
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" /> Muat Ulang
          </Button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2" data-testid="status-alert-strip">
        {FILTERS.map((f) => {
          const count = f.key === 'all' ? data?.total_reagen : data?.counts?.[f.key];
          return (
            <button
              key={f.key}
              data-testid={`status-filter-chip-${f.key}`}
              data-active={filter === f.key}
              onClick={() => setFilter(f.key)}
              className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors hover:bg-muted ${f.cls}`}
            >
              {f.label}{count !== undefined ? ` (${count})` : ''}
            </button>
          );
        })}
      </div>

      {loading && (
        <Card className="p-4" data-testid="pemantauan-loading">
          <Skeleton className="mb-3 h-8 w-full" />
          {Array.from({ length: 10 }).map((_, i) => (
            <Skeleton key={i} className="mb-2 h-6 w-full" />
          ))}
        </Card>
      )}

      {!loading && error && (
        <Card className="p-8 text-center" data-testid="pemantauan-error">
          <p className="text-sm text-destructive">{error}</p>
          <Button className="mt-3" onClick={load}>Coba Lagi</Button>
        </Card>
      )}

      {!loading && !error && data && rows.length === 0 && (
        <Card className="p-10 text-center" data-testid="pemantauan-empty-state">
          <p className="text-sm text-muted-foreground">Belum ada data untuk periode / filter ini.</p>
        </Card>
      )}

      {!loading && !error && data && rows.length > 0 && (
        <>
          <Card className="relative overflow-hidden p-0">
            <div className="ls-scroll" style={{ maxHeight: 'calc(100vh - 260px)' }}>
              <table className="w-full border-collapse text-sm" data-testid="pemantauan-table">
                <thead>
                  <tr className="text-xs uppercase tracking-wide text-muted-foreground">
                    <th className="ls-sticky-col border-b border-r px-3 py-2 text-left min-w-[220px]">
                      <button onClick={toggleSort} data-testid="sort-nama-reagen" className="inline-flex items-center gap-1 uppercase tracking-wide hover:text-foreground" title="Urutkan berdasarkan Nama Reagen">
                        Nama Reagen <SortIcon className="h-3.5 w-3.5" />
                      </button>
                    </th>
                    <th className="border-b px-2 py-2 text-right whitespace-nowrap" title="Klik nilai untuk edit manual, atau gunakan tombol Saldo Awal Otomatis">Saldo Awal ✎</th>
                    {dayCols.map((d) => {
                      const isMarked = markedDaysSet.has(d);
                      return (
                        <th
                          key={d}
                          className={`ls-day-col relative border-b py-2 ${d === todayCol ? 'ls-today' : ''} ${isKoordinator ? 'cursor-pointer hover:bg-primary/10' : ''}`}
                          title={isKoordinator
                            ? (isMarked ? `Hari ${d}: QC sudah diinput (klik untuk hapus tanda)` : `Hari ${d}: klik untuk tandai QC sudah diinput`)
                            : (isMarked ? `Hari ${d}: QC sudah diinput` : `Hari ${d}`)}
                          data-testid={isMarked ? `day-header-marked-${d}` : `day-header-${d}`}
                          onClick={() => isKoordinator && toggleMark(d)}
                        >
                          <span className={isMarked ? 'font-bold text-emerald-600' : ''}>{d}</span>
                          {isMarked && (
                            <span className="absolute left-1/2 top-0.5 h-1.5 w-1.5 -translate-x-1/2 rounded-full bg-emerald-500" data-testid={`day-mark-dot-${d}`} />
                          )}
                        </th>
                      );
                    })}
                    <th className="ls-sum-col border-b border-l py-2 text-right" title="Input manual QC (klik untuk edit)">QC ✎</th>
                    <th className="ls-sum-col border-b py-2 text-right">Total<br />Pakai</th>
                    <th className="ls-sum-col border-b py-2 text-right">Stok<br />Masuk</th>
                    <th className="ls-sum-col border-b py-2 text-right" title="Otomatis: (Saldo Awal - Total Pemakaian) + Stok Masuk">Sisa<br />Stok</th>
                    <th className="ls-sum-col border-b py-2 text-right">Buffer</th>
                    <th className="ls-sum-col border-b py-2 text-left">Satuan</th>
                    <th className="ls-sum-col border-b py-2 text-center">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.reagen_id} className={`ls-row ls-row-${r.status}`}>
                      <td className="ls-sticky-col border-b border-r px-3 py-1.5 font-medium">{r.nama_reagen}</td>
                      <EditableNumber
                        value={r.saldo_awal}
                        onSave={(v) => saveSaldo(r, v)}
                        testid={`saldo-awal-${r.reagen_id}`}
                        title={isKoordinator ? 'Klik untuk edit Saldo Awal' : 'Saldo Awal'}
                        editable={isKoordinator}
                      />
                      {dayCols.map((d) => {
                        const v = r.hari?.[String(d)] || 0;
                        if (r.is_derived) {
                          return (
                            <EditableDay
                              key={d}
                              value={v}
                              onSave={(val) => saveHari(r, d, val)}
                              testid={`hari-${r.reagen_id}-${d}`}
                              editable={isKoordinator}
                              isOverridden={Object.prototype.hasOwnProperty.call(r.hari_override || {}, String(d))}
                              isToday={d === todayCol}
                              day={d}
                            />
                          );
                        }
                        return (
                          <td key={d} className={`ls-day-col border-b py-1.5 ${v ? '' : 'text-muted-foreground/40'} ${d === todayCol ? 'ls-today' : ''}`}>{v || ''}</td>
                        );
                      })}
                      <EditableNumber
                        value={r.qc}
                        onSave={(v) => saveQc(r, v)}
                        testid={`qc-${r.reagen_id}`}
                        alignCls="ls-sum-col text-right border-l"
                        title={isKoordinator ? 'Klik untuk input manual QC' : 'QC'}
                        editable={isKoordinator}
                      />
                      <td className="num ls-sum-col border-b py-1.5 text-right font-semibold">{fmtNum(r.total_pemakaian)}</td>
                      <td className="num ls-sum-col border-b py-1.5 text-right">{fmtNum(r.stok_masuk)}</td>
                      <td
                        className={`num ls-sum-col border-b py-1.5 text-right font-semibold ${r.status === 'critical' ? 'text-red-700' : ''}`}
                        data-testid={`sisa-stok-${r.reagen_id}`}
                        title="Otomatis: (Saldo Awal - Total Pemakaian) + Stok Masuk"
                      >
                        {fmtNum(r.sisa_stock)}
                      </td>
                      <td className="num ls-sum-col border-b py-1.5 text-right text-muted-foreground">{fmtNum(r.buffer_stock)}</td>
                      <td className="ls-sum-col border-b py-1.5 text-left text-xs text-muted-foreground">{r.satuan}</td>
                      <td className="ls-sum-col border-b py-1.5 text-center"><StatusBadge status={r.status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
          <div className="space-y-1 text-xs text-muted-foreground">
            <p className="flex items-center gap-1.5">
              <Info className="h-3.5 w-3.5" />
              Menampilkan {rows.length} dari {data.total_reagen} reagen. Kolom harian 1-31 bersumber dari file LIS via Pemetaan Test. Sisa Stok (otomatis) = (Saldo Awal - Total Pemakaian) + Stok Masuk. Status {'"Perlu Cek"'} = saldo awal belum tersedia.
            </p>
            <p className="flex items-center gap-1.5">
              <Pencil className="h-3 w-3" />
              Kolom <b>Saldo Awal</b> & <b>QC</b> dapat diklik untuk input manual. <b>Sisa Stok</b> dihitung otomatis (tidak dapat diubah manual). Tombol <b>Saldo Awal Otomatis</b> mengisi saldo awal dari sisa stok bulan sebelumnya.
              Reagen turunan (mis. <b>Kit Elisa Quantiferon</b>) — kolom harian 1-31 default otomatis = Quantiferon Tube × 4, dan dapat diklik untuk diedit manual per tanggal (angka <span className="font-bold text-amber-600">tebal kuning</span> = sudah diedit manual).
              Klik nomor pada <b>header tanggal</b> (1-31) untuk menandai hari tersebut sudah di-input QC (<span className="font-bold text-emerald-600">tanda titik hijau</span>), klik lagi untuk menghapus tanda.
            </p>
          </div>
        </>
      )}
    </div>
  );
}

import React, { useEffect, useMemo, useState } from 'react';
import { usePeriod } from '../lib/period';
import { api, fmtNum } from '../lib/api';
import { StatusBadge } from '../components/StatusBadge';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import { Search, RefreshCw, Info } from 'lucide-react';

const FILTERS = [
  { key: 'all', label: 'Semua', cls: 'data-[active=true]:bg-primary data-[active=true]:text-primary-foreground' },
  { key: 'critical', label: 'Kritis', cls: 'data-[active=true]:bg-red-600 data-[active=true]:text-white' },
  { key: 'warning', label: 'Waspada', cls: 'data-[active=true]:bg-amber-500 data-[active=true]:text-slate-950' },
  { key: 'safe', label: 'Aman', cls: 'data-[active=true]:bg-emerald-600 data-[active=true]:text-white' },
  { key: 'unknown', label: 'Perlu Cek', cls: 'data-[active=true]:bg-slate-500 data-[active=true]:text-white' },
];

export default function PemantauanStok() {
  const { year, month } = usePeriod();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');
  const [q, setQ] = useState('');

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

  const rows = useMemo(() => {
    if (!data) return [];
    return data.rows.filter((r) => {
      if (filter !== 'all' && r.status !== filter) return false;
      if (q && !r.nama_reagen.toLowerCase().includes(q.toLowerCase())) return false;
      return true;
    });
  }, [data, filter, q]);

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
                    <th className="ls-sticky-col border-b border-r px-3 py-2 text-left min-w-[220px]">Nama Reagen</th>
                    <th className="border-b px-2 py-2 text-right">Saldo Awal</th>
                    {dayCols.map((d) => (
                      <th key={d} className="border-b px-1 py-2 text-center w-10">{d}</th>
                    ))}
                    <th className="border-b border-l px-2 py-2 text-right">QC</th>
                    <th className="border-b px-2 py-2 text-right">Total Pakai</th>
                    <th className="border-b px-2 py-2 text-right">Stok Masuk</th>
                    <th className="border-b px-2 py-2 text-right">Sisa Stok</th>
                    <th className="border-b px-2 py-2 text-right">Buffer</th>
                    <th className="border-b px-2 py-2 text-left">Satuan</th>
                    <th className="border-b px-2 py-2 text-center min-w-[110px]">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.reagen_id} className={`ls-row ls-row-${r.status}`}>
                      <td className="ls-sticky-col border-b border-r px-3 py-1.5 font-medium">{r.nama_reagen}</td>
                      <td className="num border-b px-2 py-1.5 text-right">{fmtNum(r.saldo_awal)}</td>
                      {dayCols.map((d) => {
                        const v = r.hari?.[String(d)] || 0;
                        return (
                          <td key={d} className={`num border-b px-1 py-1.5 text-right ${v ? '' : 'text-muted-foreground/40'}`}>{v || ''}</td>
                        );
                      })}
                      <td className="num border-b border-l px-2 py-1.5 text-right">{fmtNum(r.qc)}</td>
                      <td className="num border-b px-2 py-1.5 text-right font-semibold">{fmtNum(r.total_pemakaian)}</td>
                      <td className="num border-b px-2 py-1.5 text-right">{fmtNum(r.stok_masuk)}</td>
                      <td className={`num border-b px-2 py-1.5 text-right font-semibold ${r.status === 'critical' ? 'text-red-700' : ''}`}>{fmtNum(r.sisa_stock)}</td>
                      <td className="num border-b px-2 py-1.5 text-right text-muted-foreground">{fmtNum(r.buffer_stock)}</td>
                      <td className="border-b px-2 py-1.5 text-left text-xs text-muted-foreground">{r.satuan}</td>
                      <td className="border-b px-2 py-1.5 text-center"><StatusBadge status={r.status} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
          <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Info className="h-3.5 w-3.5" />
            Menampilkan {rows.length} dari {data.total_reagen} reagen. Sisa Stok = (Saldo Awal - Total Pemakaian) + Stok Masuk. Status "Perlu Cek" = saldo awal belum tersedia (sel #REF! pada Excel asli).
          </p>
        </>
      )}
    </div>
  );
}

import React, { useEffect, useMemo, useState } from 'react';
import { api, fmtNum } from '../lib/api';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Checkbox } from '../components/ui/checkbox';
import { Popover, PopoverContent, PopoverTrigger } from '../components/ui/popover';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Skeleton } from '../components/ui/skeleton';
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
} from 'recharts';
import { TrendingUp, BarChart3, ListFilter } from 'lucide-react';

const toISO = (d) => d.toISOString().slice(0, 10);

const rangeFor = (preset) => {
  const end = new Date();
  const start = new Date(end);
  if (preset === '7d') start.setDate(start.getDate() - 6);
  else if (preset === '30d') start.setDate(start.getDate() - 29);
  return { start: toISO(start), end: toISO(end) };
};

const TOOLTIP_STYLE = {
  backgroundColor: 'hsl(var(--card))',
  border: '1px solid hsl(var(--border))',
  borderRadius: 8,
  fontSize: 12,
  color: 'hsl(var(--foreground))',
};

export default function Analitik() {
  const [reagenList, setReagenList] = useState([]);
  const [search, setSearch] = useState('');
  const [reagenId, setReagenId] = useState('all');
  const [preset, setPreset] = useState('30d');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');
  const [comparisonMode, setComparisonMode] = useState('top10');
  const [comparisonIds, setComparisonIds] = useState([]);
  const [comparisonSearch, setComparisonSearch] = useState('');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { api.listReagen().then(setReagenList).catch(() => setReagenList([])); }, []);

  const filteredReagenList = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return reagenList;
    return reagenList.filter((r) => r.nama_reagen.toLowerCase().includes(q));
  }, [reagenList, search]);

  const comparisonFilteredList = useMemo(() => {
    const q = comparisonSearch.trim().toLowerCase();
    if (!q) return reagenList;
    return reagenList.filter((r) => r.nama_reagen.toLowerCase().includes(q));
  }, [reagenList, comparisonSearch]);

  const handlePresetChange = (val) => {
    setPreset(val);
    if (val === 'custom' && !customStart && !customEnd) {
      const r = rangeFor('30d');
      setCustomStart(r.start);
      setCustomEnd(r.end);
    }
  };

  const toggleComparisonId = (id) => {
    setComparisonIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const { start, end } = useMemo(() => (
    preset === 'custom' ? { start: customStart, end: customEnd } : rangeFor(preset)
  ), [preset, customStart, customEnd]);

  const comparisonIdsKey = comparisonIds.join(',');

  useEffect(() => {
    if (!start || !end) return;
    setLoading(true);
    const params = { start, end, reagen_id: reagenId === 'all' ? undefined : reagenId };
    if (comparisonMode === 'custom') {
      if (comparisonIds.length) params.comparison_reagen_ids = comparisonIdsKey;
    } else {
      params.comparison_limit = Number(comparisonMode.replace('top', ''));
    }
    api.analitikPemakaian(params)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [start, end, reagenId, comparisonMode, comparisonIdsKey]);

  const selectedName = reagenId === 'all' ? 'Semua Reagen' : (reagenList.find((r) => r.id === reagenId)?.nama_reagen || '');

  const trendData = (data?.trend || []).map((t) => ({
    ...t,
    label: new Date(t.date).toLocaleDateString('id-ID', { day: '2-digit', month: 'short' }),
  }));

  const showCustomEmptyPrompt = comparisonMode === 'custom' && comparisonIds.length === 0;
  const comparisonData = showCustomEmptyPrompt ? [] : (data?.comparison || []);

  return (
    <div className="space-y-4">
      <Card className="flex flex-wrap items-end gap-3 p-4" data-testid="analitik-filters">
        <div>
          <label className="mb-1 block text-xs font-medium text-muted-foreground">Reagen</label>
          <div className="flex gap-2">
            <Input
              placeholder="Cari reagen..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              data-testid="analitik-reagen-search"
              className="w-36"
            />
            <Select value={reagenId} onValueChange={setReagenId}>
              <SelectTrigger className="w-56" data-testid="analitik-reagen-select"><SelectValue /></SelectTrigger>
              <SelectContent className="max-h-72">
                <SelectItem value="all">Semua Reagen</SelectItem>
                {filteredReagenList.length === 0 ? (
                  <div className="px-2 py-1.5 text-xs text-muted-foreground">Tidak ada reagen cocok</div>
                ) : (
                  filteredReagenList.map((r) => <SelectItem key={r.id} value={r.id}>{r.nama_reagen}</SelectItem>)
                )}
              </SelectContent>
            </Select>
          </div>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-muted-foreground">Rentang Waktu</label>
          <Select value={preset} onValueChange={handlePresetChange}>
            <SelectTrigger className="w-44" data-testid="analitik-range-select"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Mingguan (7 hari)</SelectItem>
              <SelectItem value="30d">Bulanan (30 hari)</SelectItem>
              <SelectItem value="custom">Custom Tanggal</SelectItem>
            </SelectContent>
          </Select>
        </div>
        {preset === 'custom' && (
          <>
            <div>
              <label className="mb-1 block text-xs font-medium text-muted-foreground">Dari</label>
              <Input type="date" value={customStart} onChange={(e) => setCustomStart(e.target.value)} data-testid="analitik-start-date" className="w-40" />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-muted-foreground">Sampai</label>
              <Input type="date" value={customEnd} onChange={(e) => setCustomEnd(e.target.value)} data-testid="analitik-end-date" className="w-40" />
            </div>
          </>
        )}
      </Card>

      <Card className="p-4" data-testid="analitik-trend-chart">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
          <TrendingUp className="h-4 w-4 text-primary" /> Tren Pemakaian — {selectedName}
        </div>
        {loading ? (
          <Skeleton className="h-72 w-full" />
        ) : trendData.length === 0 ? (
          <p className="py-16 text-center text-sm text-muted-foreground" data-testid="analitik-trend-empty">
            Tidak ada data pemakaian pada rentang ini.
          </p>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={trendData} margin={{ left: 4, right: 12, top: 8, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
              <XAxis dataKey="label" fontSize={11} stroke="hsl(var(--muted-foreground))" />
              <YAxis fontSize={11} width={40} stroke="hsl(var(--muted-foreground))" />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [fmtNum(v), 'Pemakaian']} />
              <Line type="monotone" dataKey="jumlah" name="Pemakaian" stroke="#0d9488" strokeWidth={2.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </Card>

      <Card className="p-4" data-testid="analitik-comparison-chart">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <BarChart3 className="h-4 w-4 text-primary" /> Perbandingan Pemakaian Antar Reagen
          </div>
          <div className="flex items-center gap-2">
            <Select value={comparisonMode} onValueChange={setComparisonMode}>
              <SelectTrigger className="w-36" data-testid="analitik-comparison-mode-select"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="top5">Top 5</SelectItem>
                <SelectItem value="top10">Top 10</SelectItem>
                <SelectItem value="top20">Top 20</SelectItem>
                <SelectItem value="custom">Custom</SelectItem>
              </SelectContent>
            </Select>
            {comparisonMode === 'custom' && (
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" size="sm" data-testid="analitik-comparison-custom-button">
                    <ListFilter className="mr-1.5 h-3.5 w-3.5" />
                    {comparisonIds.length ? `${comparisonIds.length} reagen dipilih` : 'Pilih Reagen'}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-64 p-2" align="end" data-testid="analitik-comparison-popover">
                  <Input
                    placeholder="Cari reagen..."
                    value={comparisonSearch}
                    onChange={(e) => setComparisonSearch(e.target.value)}
                    data-testid="analitik-comparison-search"
                    className="mb-2 h-8"
                  />
                  <div className="max-h-56 space-y-1 overflow-y-auto">
                    {comparisonFilteredList.length === 0 ? (
                      <p className="px-1 py-2 text-xs text-muted-foreground">Tidak ada reagen cocok</p>
                    ) : (
                      comparisonFilteredList.map((r) => (
                        <label
                          key={r.id}
                          className="flex items-center gap-2 rounded px-1 py-1 text-xs hover:bg-muted"
                          data-testid={`analitik-comparison-option-${r.id}`}
                        >
                          <Checkbox
                            checked={comparisonIds.includes(r.id)}
                            onCheckedChange={() => toggleComparisonId(r.id)}
                          />
                          <span className="truncate">{r.nama_reagen}</span>
                        </label>
                      ))
                    )}
                  </div>
                </PopoverContent>
              </Popover>
            )}
          </div>
        </div>
        {loading ? (
          <Skeleton className="h-72 w-full" />
        ) : showCustomEmptyPrompt ? (
          <p className="py-16 text-center text-sm text-muted-foreground" data-testid="analitik-comparison-custom-empty">
            Pilih minimal 1 reagen pada tombol "Pilih Reagen" untuk membandingkan.
          </p>
        ) : comparisonData.length === 0 ? (
          <p className="py-16 text-center text-sm text-muted-foreground" data-testid="analitik-comparison-empty">
            Tidak ada data pemakaian pada rentang ini.
          </p>
        ) : (
          <ResponsiveContainer width="100%" height={340}>
            <BarChart data={comparisonData} layout="vertical" margin={{ left: 8, right: 24, top: 8, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="hsl(var(--border))" />
              <XAxis type="number" fontSize={11} stroke="hsl(var(--muted-foreground))" />
              <YAxis type="category" dataKey="nama_reagen" width={150} fontSize={11} stroke="hsl(var(--muted-foreground))" />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [fmtNum(v), 'Total Pemakaian']} />
              <Bar dataKey="jumlah" name="Total Pemakaian" fill="#f59e0b" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </Card>
    </div>
  );
}

import React, { useEffect, useMemo, useState } from 'react';
import { api, fmtNum } from '../lib/api';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Search, CheckCircle2, XCircle } from 'lucide-react';

export default function DataLIS() {
  const [tab, setTab] = useState('mapping');
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Data LIS mentah dan pemetaan test (read-only pada Tahap 1). Integrasi impor LIS otomatis akan ditambahkan pada tahap berikutnya.
      </p>
      <Tabs value={tab} onValueChange={setTab} data-testid="data-lis-tabs">
        <TabsList>
          <TabsTrigger value="mapping" data-testid="tab-mapping">Pemetaan Test</TabsTrigger>
          <TabsTrigger value="raw" data-testid="tab-raw">Data LIS Mentah</TabsTrigger>
        </TabsList>
        <TabsContent value="mapping" className="mt-4"><MappingTab /></TabsContent>
        <TabsContent value="raw" className="mt-4"><RawTab /></TabsContent>
      </Tabs>
    </div>
  );
}

function MappingTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('all');
  const [q, setQ] = useState('');

  useEffect(() => {
    setLoading(true);
    api.mappingTests().then(setData).finally(() => setLoading(false));
  }, []);

  const items = useMemo(() => {
    if (!data) return [];
    return data.items.filter((m) => {
      if (status !== 'all' && m.status !== status) return false;
      if (q && !(m.lis_name || '').toLowerCase().includes(q.toLowerCase())) return false;
      return true;
    });
  }, [data, status, q]);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <Badge className="bg-emerald-600 text-white">OK: {data?.ok ?? 0}</Badge>
        <Badge className="bg-slate-500 text-white">TIDAK ADA: {data?.tidak_ada ?? 0}</Badge>
        <div className="ml-auto flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input placeholder="Cari test LIS..." value={q} onChange={(e) => setQ(e.target.value)} className="h-9 w-[200px] pl-8" data-testid="mapping-search" />
          </div>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="h-9 w-[150px]" data-testid="mapping-status-filter"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Semua Status</SelectItem>
              <SelectItem value="OK">OK</SelectItem>
              <SelectItem value="TIDAK ADA">TIDAK ADA</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <Card className="p-0">
        {loading ? (
          <div className="p-4 space-y-2">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}</div>
        ) : (
          <div className="overflow-x-auto" style={{ maxHeight: 'calc(100vh - 320px)' }}>
            <table className="w-full text-sm" data-testid="mapping-table">
              <thead className="sticky top-0 bg-card">
                <tr className="text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-2 text-left">Nama Test LIS</th>
                  <th className="px-4 py-2 text-left">Nama Reagen Monitoring</th>
                  <th className="px-4 py-2 text-center">Status</th>
                </tr>
              </thead>
              <tbody>
                {items.map((m, i) => (
                  <tr key={i} className="border-t hover:bg-muted/40">
                    <td className="px-4 py-2">{m.lis_name}</td>
                    <td className="px-4 py-2 text-muted-foreground">{m.reagen_name || '—'}</td>
                    <td className="px-4 py-2 text-center">
                      {m.status === 'OK' ? (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700"><CheckCircle2 className="h-3.5 w-3.5" /> OK</span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-500"><XCircle className="h-3.5 w-3.5" /> TIDAK ADA</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
      <p className="text-xs text-muted-foreground">Menampilkan {items.length} pemetaan.</p>
    </div>
  );
}

function RawTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('2026-07');

  useEffect(() => {
    setLoading(true);
    api.lisRaw(period, 300, 0).then(setData).finally(() => setLoading(false));
  }, [period]);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Periode:</span>
        <Select value={period} onValueChange={setPeriod}>
          <SelectTrigger className="h-9 w-[150px]" data-testid="lis-period-filter"><SelectValue /></SelectTrigger>
          <SelectContent>
            {(data?.periods || ['2026-07', '2026-08']).map((p) => (
              <SelectItem key={p} value={p}>{p}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <span className="text-xs text-muted-foreground">Total {data?.total ?? 0} baris (menampilkan maks 300)</span>
      </div>
      <Card className="p-0">
        {loading ? (
          <div className="p-4 space-y-2">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}</div>
        ) : (
          <div className="overflow-auto" style={{ maxHeight: 'calc(100vh - 320px)' }}>
            <table className="w-full text-sm" data-testid="lis-raw-table">
              <thead className="sticky top-0 bg-card">
                <tr className="text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-2 text-left">Grup</th>
                  <th className="px-4 py-2 text-left">Nama Test</th>
                  <th className="px-4 py-2 text-right">Total</th>
                  <th className="px-4 py-2 text-left">Source File</th>
                </tr>
              </thead>
              <tbody>
                {(data?.items || []).map((r, i) => (
                  <tr key={i} className="border-t hover:bg-muted/40">
                    <td className="px-4 py-2 text-xs text-muted-foreground">{r.grup || '—'}</td>
                    <td className="px-4 py-2">{r.nama_test}</td>
                    <td className="num px-4 py-2 text-right font-medium">{fmtNum(r.total)}</td>
                    <td className="px-4 py-2 text-xs text-muted-foreground">{r.source_file || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

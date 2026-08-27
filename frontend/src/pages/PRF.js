import React, { useEffect, useState } from 'react';
import { usePeriod } from '../lib/period';
import { api, fmtDate } from '../lib/api';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Skeleton } from '../components/ui/skeleton';
import { FileText, Info } from 'lucide-react';

export default function PRF() {
  const { year, month } = usePeriod();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const period = `${year}-${String(month).padStart(2, '0')}`;

  useEffect(() => {
    setLoading(true);
    api.prf(period).then(setData).finally(() => setLoading(false));
  }, [period]);

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-2 rounded-lg border bg-accent/40 p-3 text-sm">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
        <p className="text-muted-foreground">
          Daftar <span className="font-medium text-foreground">Purchase Request (PRF)</span> reagen untuk periode {period}. Pada Tahap 1 data ditampilkan read-only dari hasil impor Excel. Pembuatan/edit PRF akan ditambahkan pada tahap berikutnya.
        </p>
      </div>
      <Card className="p-0">
        <div className="flex items-center gap-2 border-b px-4 py-3 text-sm font-semibold">
          <FileText className="h-4 w-4" /> PRF {period} ({data?.total ?? 0})
        </div>
        {loading ? (
          <div className="p-4 space-y-2">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}</div>
        ) : (data?.items || []).length === 0 ? (
          <div className="p-10 text-center text-sm text-muted-foreground" data-testid="prf-empty">Belum ada PRF untuk periode ini.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm" data-testid="prf-table">
              <thead>
                <tr className="text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-2 text-left">Nama Reagen</th>
                  <th className="px-4 py-2 text-center">Reagent Ke-</th>
                  <th className="px-4 py-2 text-right">Jumlah Kit</th>
                  <th className="px-4 py-2 text-left">Tanggal PR</th>
                  <th className="px-4 py-2 text-center">Status</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((p) => (
                  <tr key={p.id} className="border-t hover:bg-muted/40">
                    <td className="px-4 py-2 font-medium">{p.reagen_name}</td>
                    <td className="px-4 py-2 text-center num">{p.reagent_no}</td>
                    <td className="px-4 py-2 text-right num">{p.kits}</td>
                    <td className="px-4 py-2">{fmtDate(p.tanggal_pr)}</td>
                    <td className="px-4 py-2 text-center"><Badge variant="outline" className="text-amber-700 border-amber-300">Open</Badge></td>
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

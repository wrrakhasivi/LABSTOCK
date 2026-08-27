import React, { useEffect, useState } from 'react';
import { usePeriod } from '../lib/period';
import { api, fmtDate, fmtNum } from '../lib/api';
import { Card } from '../components/ui/card';
import { Skeleton } from '../components/ui/skeleton';
import { PackageCheck, Info } from 'lucide-react';

export default function Penerimaan() {
  const { year, month } = usePeriod();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const period = `${year}-${String(month).padStart(2, '0')}`;

  useEffect(() => {
    setLoading(true);
    api.penerimaan(period).then(setData).finally(() => setLoading(false));
  }, [period]);

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-2 rounded-lg border bg-accent/40 p-3 text-sm">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
        <p className="text-muted-foreground">
          Riwayat <span className="font-medium text-foreground">Penerimaan Barang</span> reagen periode {period}. Qty otomatis = Qty/kit × jumlah kit. Total penerimaan menambah Stok Masuk pada Pemantauan Stok.
        </p>
      </div>
      <Card className="p-0">
        <div className="flex items-center justify-between border-b px-4 py-3 text-sm font-semibold">
          <span className="flex items-center gap-2"><PackageCheck className="h-4 w-4" /> Penerimaan {period} ({data?.total ?? 0})</span>
          <span className="num text-xs font-normal text-muted-foreground">Total Qty: {fmtNum(data?.total_qty ?? 0)}</span>
        </div>
        {loading ? (
          <div className="p-4 space-y-2">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}</div>
        ) : (data?.items || []).length === 0 ? (
          <div className="p-10 text-center text-sm text-muted-foreground" data-testid="penerimaan-empty">Belum ada penerimaan untuk periode ini.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm" data-testid="penerimaan-table">
              <thead>
                <tr className="text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-2 text-left">Nama Reagen</th>
                  <th className="px-4 py-2 text-center">Reagent Ke-</th>
                  <th className="px-4 py-2 text-right">Jumlah Kit</th>
                  <th className="px-4 py-2 text-right">Qty Masuk</th>
                  <th className="px-4 py-2 text-left">Tanggal Terima</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((p) => (
                  <tr key={p.id} className="border-t hover:bg-muted/40">
                    <td className="px-4 py-2 font-medium">{p.reagen_name}</td>
                    <td className="px-4 py-2 text-center num">{p.reagent_no}</td>
                    <td className="px-4 py-2 text-right num">{p.kits}</td>
                    <td className="px-4 py-2 text-right num font-semibold">{fmtNum(p.qty)}</td>
                    <td className="px-4 py-2">{fmtDate(p.tanggal_terima)}</td>
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

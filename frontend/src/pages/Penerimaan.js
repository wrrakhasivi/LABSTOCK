import React, { useEffect, useMemo, useState } from 'react';
import { usePeriod } from '../lib/period';
import { api, fmtDate, fmtNum } from '../lib/api';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Skeleton } from '../components/ui/skeleton';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '../components/ui/dialog';
import { toast } from 'sonner';
import { PackageCheck, Info, Clock, CheckCircle2 } from 'lucide-react';

const todayStr = () => new Date().toISOString().slice(0, 10);

export default function Penerimaan() {
  const { year, month } = usePeriod();
  const [pen, setPen] = useState(null);
  const [prf, setPrf] = useState(null);
  const [loading, setLoading] = useState(true);
  const period = `${year}-${String(month).padStart(2, '0')}`;

  const [receiving, setReceiving] = useState(null);
  const [recvForm, setRecvForm] = useState({ tanggal_terima: '', kits: '' });

  const load = () => {
    setLoading(true);
    Promise.all([api.penerimaan(period), api.prf(period)])
      .then(([p, r]) => { setPen(p); setPrf(r); })
      .finally(() => setLoading(false));
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [period]);

  const pendingPrf = useMemo(() => (prf?.items || []).filter((p) => p.status !== 'received'), [prf]);

  const openReceive = (p) => {
    setReceiving(p);
    setRecvForm({ tanggal_terima: todayStr(), kits: String(p.kits ?? 1) });
  };
  const submitReceive = async () => {
    if (!recvForm.tanggal_terima) { toast.error('Isi tanggal terima'); return; }
    try {
      await api.receivePrf(receiving.id, {
        tanggal_terima: recvForm.tanggal_terima,
        kits: recvForm.kits === '' ? null : Number(recvForm.kits),
      });
      toast.success('Penerimaan tercatat — status PRF: Complete, Stok Masuk bertambah');
      setReceiving(null);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Gagal memproses penerimaan');
    }
  };

  const items = pen?.items || [];

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-2 rounded-lg border bg-accent/40 p-3 text-sm">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
        <p className="text-muted-foreground">
          Penerimaan barang periode {period} berdasarkan data PRF. Qty otomatis = Qty/kit × jumlah kit dan menambah <span className="font-medium text-foreground">Stok Masuk</span> pada Pemantauan Stok.
        </p>
      </div>

      {/* Pending PRF to receive */}
      <Card className="p-0">
        <div className="flex items-center gap-2 border-b px-4 py-3 text-sm font-semibold">
          <Clock className="h-4 w-4 text-amber-600" /> PRF Menunggu Penerimaan ({pendingPrf.length})
        </div>
        {loading ? (
          <div className="p-4 space-y-2">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}</div>
        ) : pendingPrf.length === 0 ? (
          <div className="p-6 text-center text-sm text-muted-foreground" data-testid="penerimaan-no-pending">Tidak ada PRF yang menunggu penerimaan.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm" data-testid="pending-prf-table">
              <thead>
                <tr className="text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-2 text-left">Nama Reagen</th>
                  <th className="px-4 py-2 text-center">Reagent Ke-</th>
                  <th className="px-4 py-2 text-right">Jumlah Kit</th>
                  <th className="px-4 py-2 text-left">Tanggal PR</th>
                  <th className="px-4 py-2 text-center">Aksi</th>
                </tr>
              </thead>
              <tbody>
                {pendingPrf.map((p) => (
                  <tr key={p.id} className="border-t hover:bg-muted/40">
                    <td className="px-4 py-2 font-medium">{p.reagen_name}</td>
                    <td className="px-4 py-2 text-center num">{p.reagent_no}</td>
                    <td className="px-4 py-2 text-right num">{p.kits}</td>
                    <td className="px-4 py-2">{fmtDate(p.tanggal_pr)}</td>
                    <td className="px-4 py-2 text-center">
                      <Button size="sm" variant="outline" onClick={() => openReceive(p)} data-testid={`penerimaan-terima-button-${p.id}`}>
                        <PackageCheck className="mr-1 h-3 w-3" /> Terima
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Received list */}
      <Card className="p-0">
        <div className="flex items-center justify-between border-b px-4 py-3 text-sm font-semibold">
          <span className="flex items-center gap-2"><PackageCheck className="h-4 w-4" /> Penerimaan {period} ({items.length})</span>
          <span className="num text-xs font-normal text-muted-foreground">Total Qty: {fmtNum(pen?.total_qty ?? 0)}</span>
        </div>
        {loading ? (
          <div className="p-4 space-y-2">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}</div>
        ) : items.length === 0 ? (
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
                  <th className="px-4 py-2 text-center">Sumber</th>
                  <th className="px-4 py-2 text-center">Status</th>
                </tr>
              </thead>
              <tbody>
                {items.map((p) => (
                  <tr key={p.id} className="border-t hover:bg-muted/40">
                    <td className="px-4 py-2 font-medium">{p.reagen_name}</td>
                    <td className="px-4 py-2 text-center num">{p.reagent_no}</td>
                    <td className="px-4 py-2 text-right num">{p.kits}</td>
                    <td className="px-4 py-2 text-right num font-semibold">{fmtNum(p.qty)}</td>
                    <td className="px-4 py-2">{fmtDate(p.tanggal_terima)}</td>
                    <td className="px-4 py-2 text-center">
                      <Badge variant="secondary" className="text-[10px]">{p.source === 'PRF' ? 'Dari PRF' : (p.source || 'Impor Excel')}</Badge>
                    </td>
                    <td className="px-4 py-2 text-center">
                      <Badge className="bg-emerald-600 text-white"><CheckCircle2 className="mr-1 h-3 w-3" /> Complete</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Receive dialog */}
      <Dialog open={!!receiving} onOpenChange={(o) => !o && setReceiving(null)}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader><DialogTitle>Terima Barang — {receiving?.reagen_name}</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <p className="text-xs text-muted-foreground">Reagent ke-{receiving?.reagent_no}. Status PRF akan menjadi <b>Complete</b> dan Stok Masuk bertambah.</p>
            <div>
              <Label className="text-xs">Tanggal Terima</Label>
              <Input type="date" data-testid="receive-tanggal" value={recvForm.tanggal_terima} onChange={(e) => setRecvForm({ ...recvForm, tanggal_terima: e.target.value })} className="mt-1" />
            </div>
            <div>
              <Label className="text-xs">Jumlah Kit Diterima</Label>
              <Input type="number" min="1" data-testid="receive-kits" value={recvForm.kits} onChange={(e) => setRecvForm({ ...recvForm, kits: e.target.value })} className="mt-1" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setReceiving(null)}>Batal</Button>
            <Button onClick={submitReceive} data-testid="receive-submit-button">Konfirmasi Terima</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

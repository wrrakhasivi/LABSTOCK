import React, { useEffect, useState } from 'react';
import { api, fmtNum } from '../lib/api';
import { useAuth } from '../lib/auth';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';
import { Skeleton } from '../components/ui/skeleton';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '../components/ui/dialog';
import { toast } from 'sonner';
import { Search, Pencil } from 'lucide-react';

export default function MasterReagen() {
  const { isKoordinator } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState('');
  const [editing, setEditing] = useState(null);
  const [saving, setSaving] = useState(false);

  const load = () => {
    setLoading(true);
    api.listReagen().then(setItems).finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, []);

  const filtered = items.filter((r) => r.nama_reagen.toLowerCase().includes(q.toLowerCase()));

  const save = async () => {
    setSaving(true);
    try {
      const body = {
        item_code: editing.item_code || null,
        qty_per_kit: editing.qty_per_kit === '' ? null : Number(editing.qty_per_kit),
        avg_2022: editing.avg_2022 === '' ? null : Number(editing.avg_2022),
        avg_2023: editing.avg_2023 === '' ? null : Number(editing.avg_2023),
        buffer_stock: editing.buffer_stock === '' ? null : Number(editing.buffer_stock),
        satuan: editing.satuan || 'Pcs',
      };
      await api.updateReagen(editing.id, body);
      toast.success('Reagen diperbarui');
      setEditing(null);
      load();
    } catch (e) {
      toast.error('Gagal menyimpan perubahan');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-muted-foreground">Daftar master reagen ({items.length} item). Atribut: Qty/kit, rata-rata sampel, buffer stock, satuan.</p>
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input data-testid="master-reagen-search" placeholder="Cari reagen..." value={q} onChange={(e) => setQ(e.target.value)} className="h-9 w-[220px] pl-8" />
        </div>
      </div>

      <Card className="p-0">
        {loading ? (
          <div className="p-4 space-y-2">{Array.from({ length: 10 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm" data-testid="master-reagen-table">
              <thead>
                <tr className="text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-2 text-left">Nama Reagen</th>
                  <th className="px-3 py-2 text-right">Qty/kit</th>
                  <th className="px-3 py-2 text-right">AVG 2022</th>
                  <th className="px-3 py-2 text-right">AVG 2023</th>
                  <th className="px-3 py-2 text-right">Buffer Stock</th>
                  <th className="px-3 py-2 text-left">Satuan</th>
                  {isKoordinator && <th className="px-3 py-2 text-center">Aksi</th>}
                </tr>
              </thead>
              <tbody>
                {filtered.map((r) => (
                  <tr key={r.id} className="border-t hover:bg-muted/40">
                    <td className="px-4 py-2 font-medium">{r.nama_reagen}</td>
                    <td className="num px-3 py-2 text-right">{fmtNum(r.qty_per_kit)}</td>
                    <td className="num px-3 py-2 text-right">{fmtNum(r.avg_2022)}</td>
                    <td className="num px-3 py-2 text-right">{fmtNum(r.avg_2023)}</td>
                    <td className="num px-3 py-2 text-right">{fmtNum(r.buffer_stock)}</td>
                    <td className="px-3 py-2 text-left text-muted-foreground">{r.satuan}</td>
                    {isKoordinator && (
                      <td className="px-3 py-2 text-center">
                        <Button size="sm" variant="outline" data-testid={`master-reagen-edit-button-${r.id}`} onClick={() => setEditing({ ...r, qty_per_kit: r.qty_per_kit ?? '', avg_2022: r.avg_2022 ?? '', avg_2023: r.avg_2023 ?? '', buffer_stock: r.buffer_stock ?? '', item_code: r.item_code ?? '' })}>
                          <Pencil className="mr-1 h-3 w-3" /> Edit
                        </Button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Dialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader><DialogTitle>Edit Reagen</DialogTitle></DialogHeader>
          {editing && (
            <div className="space-y-3">
              <div>
                <Label className="text-xs">Nama Reagen</Label>
                <Input value={editing.nama_reagen} disabled className="mt-1" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-xs">Qty/kit</Label>
                  <Input type="number" data-testid="edit-qty-per-kit" value={editing.qty_per_kit} onChange={(e) => setEditing({ ...editing, qty_per_kit: e.target.value })} className="mt-1" />
                </div>
                <div>
                  <Label className="text-xs">Buffer Stock</Label>
                  <Input type="number" data-testid="edit-buffer-stock" value={editing.buffer_stock} onChange={(e) => setEditing({ ...editing, buffer_stock: e.target.value })} className="mt-1" />
                </div>
                <div>
                  <Label className="text-xs">AVG Sampel 2022</Label>
                  <Input type="number" value={editing.avg_2022} onChange={(e) => setEditing({ ...editing, avg_2022: e.target.value })} className="mt-1" />
                </div>
                <div>
                  <Label className="text-xs">AVG Sampel 2023</Label>
                  <Input type="number" value={editing.avg_2023} onChange={(e) => setEditing({ ...editing, avg_2023: e.target.value })} className="mt-1" />
                </div>
                <div>
                  <Label className="text-xs">Satuan</Label>
                  <Input value={editing.satuan} onChange={(e) => setEditing({ ...editing, satuan: e.target.value })} className="mt-1" />
                </div>
                <div>
                  <Label className="text-xs">Item Code</Label>
                  <Input value={editing.item_code} onChange={(e) => setEditing({ ...editing, item_code: e.target.value })} className="mt-1" placeholder="(opsional)" />
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditing(null)}>Batal</Button>
            <Button onClick={save} disabled={saving} data-testid="master-reagen-save-button">{saving ? 'Menyimpan...' : 'Simpan'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

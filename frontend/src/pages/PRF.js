import React, { useEffect, useMemo, useState } from 'react';
import { usePeriod } from '../lib/period';
import { api, fmtDate } from '../lib/api';
import { useAuth } from '../lib/auth';
import { Card } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Skeleton } from '../components/ui/skeleton';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger,
} from '../components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../components/ui/select';
import {
  Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList,
} from '../components/ui/command';
import { Popover, PopoverContent, PopoverTrigger } from '../components/ui/popover';
import { toast } from 'sonner';
import { FileText, Info, Plus, Trash2, PackageCheck, Check, ChevronsUpDown, CheckCircle2 } from 'lucide-react';

const todayStr = () => new Date().toISOString().slice(0, 10);

function ReagenPicker({ reagens, value, onChange }) {
  const [open, setOpen] = useState(false);
  const selected = reagens.find((r) => r.id === value);
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" role="combobox" data-testid="prf-reagen-trigger" className="w-full justify-between font-normal">
          {selected ? selected.nama_reagen : 'Pilih reagen...'}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[320px] p-0" align="start">
        <Command>
          <CommandInput placeholder="Cari reagen..." />
          <CommandList>
            <CommandEmpty>Tidak ditemukan.</CommandEmpty>
            <CommandGroup>
              {reagens.map((r) => (
                <CommandItem key={r.id} value={r.nama_reagen} onSelect={() => { onChange(r.id); setOpen(false); }} data-testid={`prf-reagen-option-${r.id}`}>
                  <Check className={`mr-2 h-4 w-4 ${value === r.id ? 'opacity-100' : 'opacity-0'}`} />
                  {r.nama_reagen}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

export default function PRF() {
  const { isKoordinator } = useAuth();
  const { year, month } = usePeriod();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reagens, setReagens] = useState([]);
  const period = `${year}-${String(month).padStart(2, '0')}`;

  // create form
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ reagen_id: '', reagent_no: '1', kits: '1', tanggal_pr: '', note: '' });
  const [saving, setSaving] = useState(false);
  // receive dialog
  const [receiving, setReceiving] = useState(null);
  const [recvForm, setRecvForm] = useState({ tanggal_terima: '', kits: '' });

  const load = () => {
    setLoading(true);
    api.prf(period).then(setData).finally(() => setLoading(false));
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [period]);
  useEffect(() => { api.listReagen().then(setReagens).catch(() => {}); }, []);

  const openCreate = () => {
    const def = `${year}-${String(month).padStart(2, '0')}-01`;
    setForm({ reagen_id: '', reagent_no: '1', kits: '1', tanggal_pr: def, note: '' });
    setOpen(true);
  };

  const submit = async () => {
    if (!form.reagen_id) { toast.error('Pilih reagen dulu'); return; }
    if (!form.tanggal_pr) { toast.error('Isi tanggal PR'); return; }
    setSaving(true);
    try {
      await api.createPrf({
        reagen_id: form.reagen_id,
        reagent_no: Number(form.reagent_no),
        kits: Number(form.kits) || 1,
        tanggal_pr: form.tanggal_pr,
        note: form.note || null,
      });
      toast.success('PRF ditambahkan');
      setOpen(false);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Gagal menambah PRF');
    } finally { setSaving(false); }
  };

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
      toast.success('Barang diterima — Penerimaan tercatat & Stok Masuk bertambah');
      setReceiving(null);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Gagal memproses penerimaan');
    }
  };

  const remove = async (p) => {
    if (!window.confirm(`Hapus PRF "${p.reagen_name}"?`)) return;
    try {
      await api.deletePrf(p.id);
      toast.success('PRF dihapus');
      load();
    } catch (e) { toast.error('Gagal menghapus PRF'); }
  };

  const items = data?.items || [];

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-2 rounded-lg border bg-accent/40 p-3 text-sm">
          <Info className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
          <p className="text-muted-foreground">
            Buat <span className="font-medium text-foreground">Purchase Request (PRF)</span> pemesanan reagen untuk periode {period}. PRF yang dibuat dapat diterima di tab Penerimaan (otomatis menambah Stok Masuk).
          </p>
        </div>
        <Button onClick={openCreate} data-testid="prf-add-button" className="shrink-0" disabled={!isKoordinator} title={!isKoordinator ? 'Hanya Koordinator yang dapat menambah PRF' : undefined}>
          <Plus className="mr-1.5 h-4 w-4" /> Tambah PRF
        </Button>
      </div>

      <Card className="p-0">
        <div className="flex items-center gap-2 border-b px-4 py-3 text-sm font-semibold">
          <FileText className="h-4 w-4" /> PRF {period} ({items.length})
        </div>
        {loading ? (
          <div className="p-4 space-y-2">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}</div>
        ) : items.length === 0 ? (
          <div className="p-10 text-center text-sm text-muted-foreground" data-testid="prf-empty">Belum ada PRF untuk periode ini. Klik "Tambah PRF" untuk membuat pemesanan.</div>
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
                  {isKoordinator && <th className="px-4 py-2 text-center">Aksi</th>}
                </tr>
              </thead>
              <tbody>
                {items.map((p) => (
                  <tr key={p.id} className="border-t hover:bg-muted/40">
                    <td className="px-4 py-2 font-medium">{p.reagen_name}</td>
                    <td className="px-4 py-2 text-center num">{p.reagent_no}</td>
                    <td className="px-4 py-2 text-right num">{p.kits}</td>
                    <td className="px-4 py-2">{fmtDate(p.tanggal_pr)}</td>
                    <td className="px-4 py-2 text-center">
                      {p.status === 'received' ? (
                        <Badge className="bg-emerald-600 text-white"><CheckCircle2 className="mr-1 h-3 w-3" /> Diterima {fmtDate(p.tanggal_terima)}</Badge>
                      ) : (
                        <Badge variant="outline" className="text-amber-700 border-amber-300">Menunggu</Badge>
                      )}
                    </td>
                    {isKoordinator && (
                      <td className="px-4 py-2 text-center">
                        <div className="flex items-center justify-center gap-1">
                          {p.status !== 'received' && (
                            <Button size="sm" variant="outline" onClick={() => openReceive(p)} data-testid={`prf-receive-button-${p.id}`}>
                              <PackageCheck className="mr-1 h-3 w-3" /> Terima
                            </Button>
                          )}
                          <Button size="sm" variant="ghost" onClick={() => remove(p)} data-testid={`prf-delete-button-${p.id}`}>
                            <Trash2 className="h-3.5 w-3.5 text-destructive" />
                          </Button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Create dialog */}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader><DialogTitle>Tambah PRF (Pemesanan Reagen)</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div>
              <Label className="text-xs">Nama Reagen</Label>
              <div className="mt-1"><ReagenPicker reagens={reagens} value={form.reagen_id} onChange={(v) => setForm({ ...form, reagen_id: v })} /></div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-xs">Reagen Ke-</Label>
                <Select value={form.reagent_no} onValueChange={(v) => setForm({ ...form, reagent_no: v })}>
                  <SelectTrigger className="mt-1" data-testid="prf-reagent-no"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">Reagent ke-1</SelectItem>
                    <SelectItem value="2">Reagent ke-2</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-xs">Jumlah Kit</Label>
                <Input type="number" min="1" data-testid="prf-kits" value={form.kits} onChange={(e) => setForm({ ...form, kits: e.target.value })} className="mt-1" />
              </div>
            </div>
            <div>
              <Label className="text-xs">Tanggal PR</Label>
              <Input type="date" data-testid="prf-tanggal" value={form.tanggal_pr} onChange={(e) => setForm({ ...form, tanggal_pr: e.target.value })} className="mt-1" />
            </div>
            <div>
              <Label className="text-xs">Catatan (opsional)</Label>
              <Input data-testid="prf-note" value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} className="mt-1" placeholder="mis. urgent / CITO" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>Batal</Button>
            <Button onClick={submit} disabled={saving} data-testid="prf-submit-button">{saving ? 'Menyimpan...' : 'Simpan PRF'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Receive dialog */}
      <Dialog open={!!receiving} onOpenChange={(o) => !o && setReceiving(null)}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader><DialogTitle>Terima Barang — {receiving?.reagen_name}</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <p className="text-xs text-muted-foreground">Reagent ke-{receiving?.reagent_no}. Menandai penerimaan akan mengubah status PRF menjadi <b>Diterima</b> dan menambah Stok Masuk.</p>
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

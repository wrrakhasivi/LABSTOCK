import React, { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { useAuth } from '../lib/auth';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Skeleton } from '../components/ui/skeleton';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { Plus, Trash2, ShieldCheck, Eye } from 'lucide-react';

export default function Pengguna() {
  const { user, isKoordinator } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(null);
  const [saving, setSaving] = useState(false);

  const load = () => {
    setLoading(true);
    api.listUsers().then(setItems).finally(() => setLoading(false));
  };
  useEffect(() => { if (isKoordinator) load(); /* eslint-disable-next-line */ }, [isKoordinator]);

  if (!isKoordinator) {
    return (
      <Card className="p-10 text-center text-sm text-muted-foreground" data-testid="pengguna-access-denied">
        Halaman ini hanya dapat diakses oleh Koordinator.
      </Card>
    );
  }

  const openAdd = () => setAdding({ username: '', password: '', role: 'petugas' });

  const create = async () => {
    const username = (adding.username || '').trim();
    if (!username || !adding.password) { toast.error('Username & password wajib diisi'); return; }
    if (adding.password.length < 4) { toast.error('Password minimal 4 karakter'); return; }
    setSaving(true);
    try {
      await api.createUser({ username, password: adding.password, role: adding.role });
      toast.success(`Akun "${username}" (${adding.role}) dibuat`);
      setAdding(null);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Gagal membuat akun');
    } finally {
      setSaving(false);
    }
  };

  const remove = async (u) => {
    if (!window.confirm(`Hapus akun "${u.username}"?`)) return;
    try {
      await api.deleteUser(u.username);
      toast.success(`Akun "${u.username}" dihapus`);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Gagal menghapus akun');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">Kelola akun Petugas & Koordinator ({items.length} akun).</p>
        <Button size="sm" onClick={openAdd} data-testid="user-add-button">
          <Plus className="mr-1.5 h-4 w-4" /> Tambah Akun
        </Button>
      </div>

      <Card className="p-0">
        {loading ? (
          <div className="p-4 space-y-2">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm" data-testid="user-table">
              <thead>
                <tr className="text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-2 text-left">Username</th>
                  <th className="px-4 py-2 text-center">Role</th>
                  <th className="px-4 py-2 text-center">Aksi</th>
                </tr>
              </thead>
              <tbody>
                {items.map((u) => (
                  <tr key={u.username} className="border-t hover:bg-muted/40">
                    <td className="px-4 py-2 font-medium">{u.username}{u.username === user.username ? ' (Anda)' : ''}</td>
                    <td className="px-4 py-2 text-center">
                      <Badge className={u.role === 'koordinator' ? 'bg-emerald-600 text-white' : 'bg-slate-500 text-white'}>
                        {u.role === 'koordinator' ? <ShieldCheck className="mr-1 h-3 w-3" /> : <Eye className="mr-1 h-3 w-3" />}
                        {u.role === 'koordinator' ? 'Koordinator' : 'Petugas'}
                      </Badge>
                    </td>
                    <td className="px-4 py-2 text-center">
                      <Button
                        size="sm"
                        variant="ghost"
                        disabled={u.username === user.username}
                        onClick={() => remove(u)}
                        data-testid={`user-delete-button-${u.username}`}
                        title={u.username === user.username ? 'Tidak dapat menghapus akun sendiri' : 'Hapus akun'}
                      >
                        <Trash2 className="h-3.5 w-3.5 text-destructive" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Dialog open={!!adding} onOpenChange={(o) => !o && setAdding(null)}>
        <DialogContent className="sm:max-w-sm" data-testid="user-add-dialog">
          <DialogHeader><DialogTitle>Tambah Akun</DialogTitle></DialogHeader>
          {adding && (
            <div className="space-y-3">
              <div>
                <Label className="text-xs">Username</Label>
                <Input autoFocus data-testid="user-add-username" value={adding.username} onChange={(e) => setAdding({ ...adding, username: e.target.value })} className="mt-1" />
              </div>
              <div>
                <Label className="text-xs">Password</Label>
                <Input type="password" data-testid="user-add-password" value={adding.password} onChange={(e) => setAdding({ ...adding, password: e.target.value })} className="mt-1" />
              </div>
              <div>
                <Label className="text-xs">Role</Label>
                <Select value={adding.role} onValueChange={(v) => setAdding({ ...adding, role: v })}>
                  <SelectTrigger className="mt-1" data-testid="user-add-role"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="petugas">Petugas (lihat saja)</SelectItem>
                    <SelectItem value="koordinator">Koordinator (akses penuh)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setAdding(null)}>Batal</Button>
            <Button onClick={create} disabled={saving} data-testid="user-add-save-button">{saving ? 'Menyimpan...' : 'Tambah'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

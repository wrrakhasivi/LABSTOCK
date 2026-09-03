import React, { useState } from 'react';
import { toast } from 'sonner';
import { KeyRound, Loader2 } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger } from './ui/dialog';
import { api } from '../lib/api';
import { useAuth } from '../lib/auth';

export const ChangePasswordButton = () => {
  const { logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ current_password: '', new_password: '', confirm: '' });
  const [busy, setBusy] = useState(false);

  const reset = () => setForm({ current_password: '', new_password: '', confirm: '' });

  const submit = async () => {
    if (!form.current_password || !form.new_password) { toast.error('Lengkapi semua field'); return; }
    if (form.new_password.length < 4) { toast.error('Password baru minimal 4 karakter'); return; }
    if (form.new_password !== form.confirm) { toast.error('Konfirmasi password tidak cocok'); return; }
    setBusy(true);
    try {
      await api.changePassword({ current_password: form.current_password, new_password: form.new_password });
      toast.success('Password berhasil diubah. Silakan login kembali dengan password baru.');
      setOpen(false);
      reset();
      logout();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Gagal mengubah password');
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(o) => { setOpen(o); if (!o) reset(); }}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm" data-testid="change-password-button" title="Ganti Password">
          <KeyRound className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-sm" data-testid="change-password-dialog">
        <DialogHeader><DialogTitle>Ganti Password</DialogTitle></DialogHeader>
        <div className="space-y-3">
          <div>
            <Label className="text-xs">Password Lama</Label>
            <Input type="password" data-testid="change-password-current" value={form.current_password} onChange={(e) => setForm({ ...form, current_password: e.target.value })} className="mt-1" />
          </div>
          <div>
            <Label className="text-xs">Password Baru</Label>
            <Input type="password" data-testid="change-password-new" value={form.new_password} onChange={(e) => setForm({ ...form, new_password: e.target.value })} className="mt-1" />
          </div>
          <div>
            <Label className="text-xs">Konfirmasi Password Baru</Label>
            <Input type="password" data-testid="change-password-confirm" value={form.confirm} onChange={(e) => setForm({ ...form, confirm: e.target.value })} className="mt-1" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>Batal</Button>
          <Button onClick={submit} disabled={busy} data-testid="change-password-submit">
            {busy ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Menyimpan...</> : 'Simpan'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

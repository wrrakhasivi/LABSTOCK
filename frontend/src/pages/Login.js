import React, { useState } from 'react';
import { useAuth } from '../lib/auth';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';
import { FlaskConical, Loader2 } from 'lucide-react';

export default function Login() {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      await login(username, password);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Username atau password salah');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 px-4">
      <Card className="w-full max-w-sm p-6" data-testid="login-card">
        <div className="mb-6 flex flex-col items-center gap-2">
          <div className="flex h-12 w-12 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <FlaskConical className="h-6 w-6" />
          </div>
          <div className="text-center">
            <div className="text-lg font-bold tracking-tight">LabStock</div>
            <div className="text-xs text-muted-foreground">Masuk untuk mengakses Pemantauan Stok Reagen Lab PK</div>
          </div>
        </div>
        <form onSubmit={submit} className="space-y-3">
          <div>
            <Label className="text-xs">Username</Label>
            <Input
              data-testid="login-username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="mt-1"
              autoFocus
              autoComplete="username"
            />
          </div>
          <div>
            <Label className="text-xs">Password</Label>
            <Input
              data-testid="login-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1"
              autoComplete="current-password"
            />
          </div>
          {error && <p className="text-xs text-red-600" data-testid="login-error">{error}</p>}
          <Button type="submit" className="w-full" disabled={busy || !username || !password} data-testid="login-submit-button">
            {busy ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Memproses...</> : 'Masuk'}
          </Button>
        </form>
        <p className="mt-4 text-center text-[11px] text-muted-foreground">
          Petugas: hanya dapat melihat data. Koordinator: akses penuh (tambah/edit/hapus).
        </p>
      </Card>
    </div>
  );
}

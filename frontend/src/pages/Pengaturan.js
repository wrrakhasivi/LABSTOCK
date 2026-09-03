import React, { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { api } from '../lib/api';
import { useAuth } from '../lib/auth';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Skeleton } from '../components/ui/skeleton';
import { FileClock, Trash2 } from 'lucide-react';

export default function Pengaturan() {
  const { isKoordinator } = useAuth();
  const [settings, setSettings] = useState(null);
  const [days, setDays] = useState('7');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const load = () => {
    setLoading(true);
    api.getSettings().then((s) => { setSettings(s); setDays(String(s.lis_retention_days)); }).finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, []);

  if (!isKoordinator) {
    return (
      <Card className="p-10 text-center text-sm text-muted-foreground" data-testid="pengaturan-access-denied">
        Halaman ini hanya dapat diakses oleh Koordinator.
      </Card>
    );
  }

  const save = async () => {
    setSaving(true);
    try {
      await api.updateSettings({ lis_retention_days: Number(days) });
      toast.success(`Periode retensi file mentah LIS disetel ke ${days} hari`);
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Gagal menyimpan pengaturan');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-xl space-y-4">
      <Card className="p-5" data-testid="retention-settings-card">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
            <Trash2 className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold">Auto-Hapus File Mentah Excel LIS</h3>
            <p className="mt-1 text-xs text-muted-foreground">
              File Excel LIS yang sudah diimpor (tab "Data LIS Mentah") akan dihapus otomatis setelah
              periode ini sejak tanggal upload, untuk meringankan server. Data pemakaian & stok yang
              sudah masuk ke Pemantauan Stok <b>tidak terpengaruh</b> — hanya arsip mentahnya yang dihapus.
            </p>
          </div>
        </div>

        {loading ? (
          <Skeleton className="mt-4 h-10 w-48" />
        ) : (
          <div className="mt-4 flex items-center gap-3">
            <Select value={days} onValueChange={setDays}>
              <SelectTrigger className="w-40" data-testid="retention-days-select"><SelectValue /></SelectTrigger>
              <SelectContent>
                {(settings?.allowed_retention_days || [3, 7, 30]).map((d) => (
                  <SelectItem key={d} value={String(d)}>{d} hari</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button size="sm" onClick={save} disabled={saving} data-testid="retention-save-button">
              {saving ? 'Menyimpan...' : 'Simpan'}
            </Button>
          </div>
        )}

        {settings?.last_cleanup && (
          <p className="mt-4 flex items-center gap-1.5 text-xs text-muted-foreground" data-testid="retention-last-cleanup">
            <FileClock className="h-3.5 w-3.5" />
            Terakhir dibersihkan: {new Date(settings.last_cleanup.created_at).toLocaleString('id-ID')} ·{' '}
            {settings.last_cleanup.deleted} baris dihapus (retensi {settings.last_cleanup.retention_days} hari)
          </p>
        )}
      </Card>
    </div>
  );
}

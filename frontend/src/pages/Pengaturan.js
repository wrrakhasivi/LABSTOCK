import React, { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { useAuth } from '../lib/auth';
import { Card } from '../components/ui/card';
import { Skeleton } from '../components/ui/skeleton';
import { ShieldCheck, FileClock } from 'lucide-react';

export default function Pengaturan() {
  const { isKoordinator } = useAuth();
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getSettings().then(setSettings).finally(() => setLoading(false));
  }, []);

  if (!isKoordinator) {
    return (
      <Card className="p-10 text-center text-sm text-muted-foreground" data-testid="pengaturan-access-denied">
        Halaman ini hanya dapat diakses oleh Koordinator.
      </Card>
    );
  }

  return (
    <div className="max-w-xl space-y-4">
      <Card className="p-5" data-testid="data-permanence-card">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-emerald-500/10 text-emerald-600">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold">Data Tersimpan Permanen</h3>
            <p className="mt-1 text-xs text-muted-foreground">
              Semua data (Saldo Awal, QC, PRF, Penerimaan, edit harian, dan data mentah Data LIS
              yang diimpor) disimpan permanen di database MongoDB. Kolom harian 1-31 pada
              Pemantauan Stok dihitung langsung dari data ini, sehingga <b>tidak ada fitur auto-hapus</b>{' '}
              yang berjalan — data tidak akan hilang saat server restart, deployment ulang, atau saat
              periode baru dibuat. Data hanya terhapus bila dihapus manual oleh Koordinator (mis. hapus
              source file LIS atau hapus periode).
            </p>
          </div>
        </div>
        {loading ? (
          <Skeleton className="mt-4 h-6 w-64" />
        ) : settings?.last_cleanup ? (
          <p className="mt-4 flex items-center gap-1.5 text-xs text-muted-foreground" data-testid="retention-last-cleanup-history">
            <FileClock className="h-3.5 w-3.5" />
            Riwayat pembersihan otomatis (fitur lama, sudah dinonaktifkan): terakhir{' '}
            {new Date(settings.last_cleanup.created_at).toLocaleString('id-ID')} ·{' '}
            {settings.last_cleanup.deleted} baris dihapus.
          </p>
        ) : null}
      </Card>
    </div>
  );
}

import React, { useState } from 'react';
import { toast } from 'sonner';
import { Download, Trash2 } from 'lucide-react';
import { Button } from './ui/button';
import { Checkbox } from './ui/checkbox';
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription,
  AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from './ui/alert-dialog';
import { api, MONTHS_ID } from '../lib/api';
import { usePeriod } from '../lib/period';

export const ExportButton = ({ year, month }) => {
  const [busy, setBusy] = useState(false);
  const run = async () => {
    setBusy(true);
    try {
      const blob = await api.exportMonitoring(year, month);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Pemantauan_Stok_${MONTHS_ID[month]}_${year}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Laporan Excel diunduh');
    } catch (e) { toast.error('Gagal mengekspor laporan'); } finally { setBusy(false); }
  };
  return (
    <Button variant="outline" size="sm" onClick={run} disabled={busy} data-testid="export-excel-button" title="Unduh laporan Excel bulan ini">
      <Download className="mr-1.5 h-3.5 w-3.5" /> {busy ? 'Menyiapkan...' : 'Ekspor Excel'}
    </Button>
  );
};

export const DeletePeriodButton = ({ year, month, label }) => {
  const { refreshPeriods, setYear, setMonth } = usePeriod();
  const [open, setOpen] = useState(false);
  const [info, setInfo] = useState(null);
  const [hapusLis, setHapusLis] = useState(false);
  const [busy, setBusy] = useState(false);

  const openDialog = async () => {
    setHapusLis(false);
    setInfo(null);
    setOpen(true);
    try { setInfo(await api.periodeInfo(year, month)); } catch (e) { setInfo({}); }
  };

  const run = async () => {
    setBusy(true);
    try {
      const res = await api.hapusPeriode(year, month, hapusLis);
      toast.success(`Periode ${res.label} dihapus (${res.deleted.stock_period} reagen${hapusLis ? `, ${res.deleted.lis_raw} data LIS` : ''})`);
      setOpen(false);
      const list = await refreshPeriods();
      if (list?.length) { setYear(list[0].year); setMonth(list[0].month); }
    } catch (e) { toast.error('Gagal menghapus periode'); } finally { setBusy(false); }
  };

  return (
    <>
      <Button variant="outline" size="sm" onClick={openDialog} className="text-red-700 hover:text-red-800" data-testid="delete-period-button" title="Hapus periode ini">
        <Trash2 className="mr-1.5 h-3.5 w-3.5" /> Hapus Periode
      </Button>
      <AlertDialog open={open} onOpenChange={setOpen}>
        <AlertDialogContent data-testid="delete-period-dialog">
          <AlertDialogHeader>
            <AlertDialogTitle>Hapus periode {label}?</AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="space-y-2 text-sm text-muted-foreground">
                <p>Saldo Awal, QC, dan penyesuaian per reagen pada periode ini akan dihapus. Periode akan hilang dari daftar bulan.</p>
                {info && (
                  <ul className="list-disc pl-5" data-testid="delete-period-info">
                    <li>{info.stock_period ?? 0} data saldo/QC reagen</li>
                    <li>{info.lis_raw ?? 0} baris data LIS{(info.lis_raw ?? 0) > 0 && !hapusLis ? ' (tetap disimpan)' : ''}</li>
                    <li>{info.prf ?? 0} PRF, {info.penerimaan ?? 0} penerimaan (tetap disimpan)</li>
                  </ul>
                )}
                {(info?.lis_raw ?? 0) > 0 && (
                  <label className="flex items-center gap-2 pt-1 text-foreground">
                    <Checkbox checked={hapusLis} onCheckedChange={(v) => setHapusLis(!!v)} data-testid="delete-period-lis-checkbox" />
                    Ikut hapus data LIS bulan ini
                  </label>
                )}
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="delete-period-cancel">Batal</AlertDialogCancel>
            <AlertDialogAction className="bg-red-600 hover:bg-red-700" onClick={(e) => { e.preventDefault(); run(); }} disabled={busy || !info} data-testid="delete-period-confirm">
              {busy ? 'Menghapus...' : 'Hapus'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

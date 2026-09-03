import React, { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { Card } from '../components/ui/card';
import { Skeleton } from '../components/ui/skeleton';
import { Badge } from '../components/ui/badge';
import { FileSpreadsheet, Layers, Columns3, Calculator, Palette, Database, StickyNote, Clock } from 'lucide-react';

const Section = ({ icon: Icon, title, children }) => (
  <Card className="p-5">
    <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
      <Icon className="h-4 w-4 text-primary" /> {title}
    </div>
    {children}
  </Card>
);

const statusColorCls = (w) => {
  const s = (w || '').toLowerCase();
  if (s.includes('merah')) return 'bg-red-600 text-white';
  if (s.includes('kuning')) return 'bg-amber-500 text-slate-950';
  if (s.includes('hijau')) return 'bg-emerald-600 text-white';
  return 'bg-slate-200 text-slate-800';
};

export default function AnalisisExcel() {
  const [d, setD] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.excelSummary().then(setD).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-32 w-full" />)}</div>;
  if (!d) return <Card className="p-8 text-center text-sm text-muted-foreground">Ringkasan tidak tersedia.</Card>;

  return (
    <div className="space-y-4" data-testid="analisis-excel-page">
      <div className="rounded-xl border bg-gradient-to-r from-slate-50 via-teal-50 to-slate-50 p-5 dark:from-slate-900 dark:via-teal-950 dark:to-slate-900">
        <div className="flex items-center gap-2 text-sm font-semibold"><FileSpreadsheet className="h-4 w-4 text-primary" /> {d.file}</div>
        <p className="mt-2 max-w-3xl text-sm text-muted-foreground">{d.ringkasan}</p>
      </div>

      <Section icon={Layers} title="Sheet yang Digunakan">
        <div className="grid gap-3 sm:grid-cols-2">
          {d.sheets.map((s, i) => (
            <div key={i} className="rounded-lg border p-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">{s.nama}</span>
                <Badge variant="outline" className="text-[10px]">{s.peran}</Badge>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">{s.keterangan}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section icon={Columns3} title="Kolom Sheet Pemantauan">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-xs uppercase tracking-wide text-muted-foreground"><th className="px-3 py-2 text-left">Kolom</th><th className="px-3 py-2 text-left">Arti</th></tr></thead>
            <tbody>
              {d.kolom_monitoring.map((k, i) => (
                <tr key={i} className="border-t"><td className="px-3 py-2 font-medium whitespace-nowrap">{k.kolom}</td><td className="px-3 py-2 text-muted-foreground">{k.arti}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      <div className="grid gap-4 lg:grid-cols-2">
        <Section icon={Calculator} title="Rumus Perhitungan">
          <div className="space-y-2">
            {d.rumus.map((r, i) => (
              <div key={i} className="rounded-md border p-2">
                <div className="text-sm font-medium">{r.nama}</div>
                <code className="num text-xs text-primary">{r.rumus}</code>
              </div>
            ))}
          </div>
        </Section>

        <Section icon={Palette} title="Status & Warna Peringatan">
          <div className="space-y-2">
            {d.status_warna.map((s, i) => (
              <div key={i} className="rounded-md border p-2">
                <div className="flex items-center gap-2">
                  <span className={`rounded px-2 py-0.5 text-[11px] font-semibold ${statusColorCls(s.warna)}`}>{s.status}</span>
                  <code className="num text-xs">{s.aturan}</code>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{s.tindakan}</p>
              </div>
            ))}
          </div>
        </Section>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Section icon={Clock} title="Status PRF (berdasarkan tanggal)">
          <div className="space-y-2">
            {d.status_prf.map((s, i) => (
              <div key={i} className="flex items-start gap-2 rounded-md border p-2 text-xs">
                <span className="font-medium text-foreground">{s.kondisi}:</span>
                <span className="text-muted-foreground">{s.arti}</span>
              </div>
            ))}
          </div>
        </Section>

        <Section icon={Database} title="Entitas Database">
          <div className="flex flex-wrap gap-2">
            {d.entitas_database.map((e, i) => (
              <Badge key={i} variant="secondary" className="text-xs">{e}</Badge>
            ))}
          </div>
        </Section>
      </div>

      <Section icon={StickyNote} title="Catatan Penting">
        <p className="text-sm text-muted-foreground">{d.catatan}</p>
      </Section>
    </div>
  );
}

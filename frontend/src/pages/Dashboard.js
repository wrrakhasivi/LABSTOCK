import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { usePeriod } from '../lib/period';
import { api, fmtNum } from '../lib/api';
import { Card } from '../components/ui/card';
import { Skeleton } from '../components/ui/skeleton';
import { StatusBadge } from '../components/StatusBadge';
import { WhatsAppCard } from '../components/WhatsAppCard';
import {
  FlaskConical, AlertTriangle, AlertCircle, CheckCircle2, HelpCircle,
  Table2, Database, BookOpen, ArrowRight, PackageCheck, FileText,
} from 'lucide-react';

const KPIS = [
  { key: 'total_reagen', label: 'Total Reagen', accent: 'bg-primary', Icon: FlaskConical, isTotal: true },
  { key: 'critical', label: 'Kritis', accent: 'bg-red-600', Icon: AlertTriangle },
  { key: 'warning', label: 'Waspada', accent: 'bg-amber-500', Icon: AlertCircle },
  { key: 'safe', label: 'Aman', accent: 'bg-emerald-600', Icon: CheckCircle2 },
  { key: 'unknown', label: 'Perlu Cek', accent: 'bg-slate-400', Icon: HelpCircle },
];

const QUICK = [
  { to: '/pemantauan', label: 'Pemantauan Stok', desc: 'Lihat tabel pemakaian harian & sisa stok', Icon: Table2 },
  { to: '/master-reagen', label: 'Master Reagen', desc: 'Kelola data reagen & buffer stock', Icon: FlaskConical },
  { to: '/data-lis', label: 'Data LIS', desc: 'Data LIS mentah & pemetaan test', Icon: Database },
  { to: '/prf', label: 'PRF', desc: 'Daftar purchase request reagen', Icon: FileText },
  { to: '/penerimaan', label: 'Penerimaan', desc: 'Riwayat penerimaan barang', Icon: PackageCheck },
  { to: '/analisis-excel', label: 'Analisis Excel', desc: 'Ringkasan struktur & rumus Excel', Icon: BookOpen },
];

export default function Dashboard() {
  const { year, month } = usePeriod();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.monitoring(year, month)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [year, month]);

  const critical = (data?.rows || []).filter((r) => r.status === 'critical').slice(0, 10);

  return (
    <div className="space-y-6">
      {/* Hero */}
      <div className="rounded-xl border bg-gradient-to-r from-slate-50 via-teal-50 to-slate-50 p-5">
        <h2 className="text-xl font-bold tracking-tight sm:text-2xl">Selamat datang di LabStock</h2>
        <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
          Sistem pemantauan stok reagen Laboratorium Patologi Klinik. Menggantikan file Excel
          pemantauan dengan penyimpanan berbasis tanggal — dapat dipakai lintas bulan & tahun.
          Periode aktif: <span className="font-semibold text-foreground">{data?.label || `${month}/${year}`}</span>.
        </p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {KPIS.map((k) => {
          const val = k.isTotal ? data?.total_reagen : data?.counts?.[k.key];
          const Icon = k.Icon;
          return (
            <Card key={k.key} className="relative overflow-hidden p-4" data-testid={`kpi-${k.key}`}>
              <div className={`absolute inset-y-0 left-0 w-1 ${k.accent}`} />
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-muted-foreground">{k.label}</span>
                <Icon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="num mt-2 text-3xl font-bold">
                {loading ? <Skeleton className="h-8 w-12" /> : (val ?? 0)}
              </div>
            </Card>
          );
        })}
      </div>

      <WhatsAppCard year={year} month={month} />

      {/* Critical table */}
      <Card className="p-0">
        <div className="flex items-center justify-between border-b px-4 py-3">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <AlertTriangle className="h-4 w-4 text-red-600" /> Reagen Kritis ({data?.counts?.critical ?? 0})
          </div>
          <Link to="/pemantauan" className="flex items-center gap-1 text-xs text-primary hover:underline" data-testid="link-lihat-semua">
            Lihat semua <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
        {loading ? (
          <div className="p-4"><Skeleton className="h-24 w-full" /></div>
        ) : critical.length === 0 ? (
          <div className="p-8 text-center text-sm text-muted-foreground">Tidak ada reagen berstatus kritis pada periode ini.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-2 text-left">Nama Reagen</th>
                  <th className="px-4 py-2 text-right">Sisa Stok</th>
                  <th className="px-4 py-2 text-right">Buffer</th>
                  <th className="px-4 py-2 text-center">Status</th>
                </tr>
              </thead>
              <tbody>
                {critical.map((r) => (
                  <tr key={r.reagen_id} className="border-t hover:bg-muted/40">
                    <td className="px-4 py-2 font-medium">{r.nama_reagen}</td>
                    <td className="num px-4 py-2 text-right font-semibold text-red-700">{fmtNum(r.sisa_stock)}</td>
                    <td className="num px-4 py-2 text-right text-muted-foreground">{fmtNum(r.buffer_stock)}</td>
                    <td className="px-4 py-2 text-center"><StatusBadge status={r.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Quick links */}
      <div>
        <h3 className="mb-2 text-sm font-semibold text-muted-foreground">Akses Cepat</h3>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {QUICK.map((q) => {
            const Icon = q.Icon;
            return (
              <Link key={q.to} to={q.to} data-testid={`quicklink-${q.to.replace('/', '') || 'home'}`}>
                <Card className="group flex items-center gap-3 p-4 transition-colors hover:border-primary hover:bg-accent/40">
                  <div className="flex h-10 w-10 items-center justify-center rounded-md bg-accent text-accent-foreground">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-medium">{q.label}</div>
                    <div className="text-xs text-muted-foreground">{q.desc}</div>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-1" />
                </Card>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { api, fmtNum } from '../lib/api';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Skeleton } from '../components/ui/skeleton';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Label } from '../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { toast } from 'sonner';
import { Search, CheckCircle2, XCircle, Upload, FileSpreadsheet, AlertTriangle, Loader2, Pencil, Trash2, FileX } from 'lucide-react';

export default function DataLIS() {
  const [tab, setTab] = useState('import');
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Import data LIS harian (Excel), lihat data mentah, dan pemetaan test ke reagen. Import LIS otomatis memperbarui pemakaian harian & sisa stok pada Pemantauan Stok.
      </p>
      <Tabs value={tab} onValueChange={setTab} data-testid="data-lis-tabs">
        <TabsList>
          <TabsTrigger value="import" data-testid="tab-import">Import LIS</TabsTrigger>
          <TabsTrigger value="raw" data-testid="tab-raw">Data LIS Mentah</TabsTrigger>
          <TabsTrigger value="mapping" data-testid="tab-mapping">Pemetaan Test</TabsTrigger>
        </TabsList>
        <TabsContent value="import" className="mt-4"><ImportTab /></TabsContent>
        <TabsContent value="raw" className="mt-4"><RawTab /></TabsContent>
        <TabsContent value="mapping" className="mt-4"><MappingTab /></TabsContent>
      </Tabs>
    </div>
  );
}

function ImportTab() {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const inputRef = useRef(null);

  const onPick = (e) => setFiles(Array.from(e.target.files || []));

  const doImport = async () => {
    if (!files.length) { toast.error('Pilih minimal 1 file Excel'); return; }
    setUploading(true);
    setResult(null);
    try {
      const res = await api.lisImport(files);
      setResult(res);
      toast.success(`Import selesai: ${res.pemakaian_records} pemakaian, ${res.reagen_terdampak} reagen terdampak`);
      setFiles([]);
      if (inputRef.current) inputRef.current.value = '';
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Gagal import LIS');
    } finally { setUploading(false); }
  };

  return (
    <div className="space-y-4">
      <Card className="p-5">
        <div className="mb-3 flex items-center gap-2 text-sm font-semibold"><Upload className="h-4 w-4 text-primary" /> Import File LIS (Excel)</div>
        <div className="rounded-lg border-2 border-dashed p-6 text-center">
          <FileSpreadsheet className="mx-auto h-8 w-8 text-muted-foreground" />
          <p className="mt-2 text-sm text-muted-foreground">Pilih satu atau beberapa file Excel LIS (.xlsx / .xls). Bisa 1 hari, 3 hari, 7 hari, atau 1 bulan.</p>
          <input
            ref={inputRef}
            type="file"
            accept=".xlsx,.xlsm,.xls"
            multiple
            onChange={onPick}
            data-testid="lis-file-input"
            className="mt-3 block w-full cursor-pointer text-sm file:mr-3 file:rounded-md file:border-0 file:bg-primary file:px-4 file:py-2 file:text-primary-foreground hover:file:opacity-90"
          />
          {files.length > 0 && (
            <div className="mt-3 flex flex-wrap justify-center gap-2" data-testid="lis-selected-files">
              {files.map((f, i) => <Badge key={i} variant="secondary">{f.name}</Badge>)}
            </div>
          )}
          <Button className="mt-4" onClick={doImport} disabled={uploading || !files.length} data-testid="lis-import-button">
            {uploading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Mengimpor...</> : <><Upload className="mr-2 h-4 w-4" /> Import Sekarang</>}
          </Button>
        </div>
        <div className="mt-4 rounded-md bg-muted/50 p-3 text-xs text-muted-foreground">
          <p className="font-medium text-foreground">Format nama file: <code className="num">LIS_YYMMDD</code></p>
          <p>Contoh: <code className="num">LIS_260802</code> = 2 Agustus 2026, <code className="num">LIS_260925</code> = 25 September 2026.</p>
          <p className="mt-1">Isi file: kolom <b>Nama Test</b> dan <b>Jumlah</b> (opsional <b>Grup</b>). Test dicocokkan ke reagen via Pemetaan Test (1 test = 1 pemakaian reagen).</p>
          <p className="mt-1 font-medium text-foreground">Penempatan tanggal 1-31 fleksibel:</p>
          <ul className="ml-4 list-disc space-y-0.5">
            <li>Ada kolom <b>Tanggal</b> per baris → pemakaian mengikuti tanggal tiap baris (mis. file <code className="num">LIS_260831</code> untuk 1 bulan penuh).</li>
            <li>Ada kolom hari <b>1-31</b> (format matriks) → tersebar otomatis ke tiap tanggal.</li>
            <li>Tanpa keduanya → seluruh data memakai tanggal dari nama file.</li>
          </ul>
        </div>
      </Card>

      {result && (
        <Card className="p-5" data-testid="lis-import-result">
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold"><CheckCircle2 className="h-4 w-4 text-emerald-600" /> Hasil Import</div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Stat label="File" value={result.files.length} />
            <Stat label="Tanggal Terisi" value={result.dates_affected.length} />
            <Stat label="Pemakaian Tercatat" value={result.pemakaian_records} />
            <Stat label="Reagen Terdampak" value={result.reagen_terdampak} />
          </div>
          <div className="mt-4 space-y-2">
            {result.files.map((f, i) => (
              <div key={i} className="rounded-md border p-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{f.filename}</span>
                  {f.error ? <Badge className="bg-red-600 text-white">Error</Badge> : <Badge variant="secondary">{f.dates?.join(', ')}</Badge>}
                </div>
                {f.error ? (
                  <p className="mt-1 text-xs text-destructive">{f.error}</p>
                ) : (
                  <p className="mt-1 text-xs text-muted-foreground">{f.tests} test dibaca, {f.matched} cocok ke reagen{f.unmatched?.length ? `, ${f.unmatched.length} tidak cocok` : ''}.</p>
                )}
                {f.warnings?.length ? <p className="mt-1 text-xs text-amber-600">{f.warnings.join('; ')}</p> : null}
              </div>
            ))}
          </div>
          {result.unmatched_tests?.length > 0 && (
            <div className="mt-3 rounded-md border border-amber-300 bg-amber-50 p-3">
              <div className="flex items-center gap-1.5 text-xs font-medium text-amber-800"><AlertTriangle className="h-3.5 w-3.5" /> Test tidak dikenali ({result.unmatched_tests.length}) — tidak masuk perhitungan:</div>
              <div className="mt-2 flex flex-wrap gap-1">
                {result.unmatched_tests.map((t, i) => <Badge key={i} variant="outline" className="text-[10px]">{t}</Badge>)}
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

const Stat = ({ label, value }) => (
  <div className="rounded-md border p-3">
    <div className="text-xs text-muted-foreground">{label}</div>
    <div className="num text-2xl font-bold">{value}</div>
  </div>
);


function MappingTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState('all');
  const [q, setQ] = useState('');
  const [reagenNames, setReagenNames] = useState([]);
  const [editing, setEditing] = useState(null);
  const [saving, setSaving] = useState(false);

  const load = () => {
    setLoading(true);
    api.mappingTests().then(setData).finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, []);
  useEffect(() => { api.listReagen().then((rs) => setReagenNames(rs.map((r) => r.nama_reagen))).catch(() => {}); }, []);

  const items = useMemo(() => {
    if (!data) return [];
    return data.items.filter((m) => {
      if (status !== 'all' && m.status !== status) return false;
      if (q && !(m.lis_name || '').toLowerCase().includes(q.toLowerCase())) return false;
      return true;
    });
  }, [data, status, q]);

  const save = async () => {
    setSaving(true);
    try {
      const res = await api.updateMapping(editing.id, {
        reagen_name: editing.reagen_name || '',
        status: editing.status,
      });
      const s = res?.sync || res?.data?.sync;
      if (s?.action === 'renamed') toast.success(`Master Reagen "${s.from}" diubah menjadi "${s.nama_reagen}"`);
      else if (s?.action === 'created') toast.success(`Master Reagen baru "${s.nama_reagen}" dibuat`);
      else toast.success('Pemetaan diperbarui');
      setEditing(null);
      load();
    } catch (e) {
      toast.error('Gagal menyimpan pemetaan');
    } finally { setSaving(false); }
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <Badge className="bg-emerald-600 text-white">OK: {data?.ok ?? 0}</Badge>
        <Badge className="bg-slate-500 text-white">TIDAK ADA: {data?.tidak_ada ?? 0}</Badge>
        <div className="ml-auto flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input placeholder="Cari test LIS..." value={q} onChange={(e) => setQ(e.target.value)} className="h-9 w-[200px] pl-8" data-testid="mapping-search" />
          </div>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="h-9 w-[150px]" data-testid="mapping-status-filter"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Semua Status</SelectItem>
              <SelectItem value="OK">OK</SelectItem>
              <SelectItem value="TIDAK ADA">TIDAK ADA</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <Card className="p-0">
        {loading ? (
          <div className="p-4 space-y-2">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}</div>
        ) : (
          <div className="overflow-x-auto" style={{ maxHeight: 'calc(100vh - 320px)' }}>
            <table className="w-full text-sm" data-testid="mapping-table">
              <thead className="sticky top-0 bg-card">
                <tr className="text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-2 text-left">Nama Test LIS</th>
                  <th className="px-4 py-2 text-left">Nama Reagen Monitoring</th>
                  <th className="px-4 py-2 text-center">Status</th>
                  <th className="px-4 py-2 text-center">Aksi</th>
                </tr>
              </thead>
              <tbody>
                {items.map((m) => (
                  <tr key={m.id} className="border-t hover:bg-muted/40">
                    <td className="px-4 py-2">{m.lis_name}</td>
                    <td className="px-4 py-2 text-muted-foreground">{m.reagen_name || '—'}</td>
                    <td className="px-4 py-2 text-center">
                      {m.status === 'OK' ? (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700"><CheckCircle2 className="h-3.5 w-3.5" /> OK</span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-500"><XCircle className="h-3.5 w-3.5" /> TIDAK ADA</span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-center">
                      <Button size="sm" variant="outline" data-testid={`mapping-edit-button-${m.id}`} onClick={() => setEditing({ ...m, reagen_name: m.reagen_name || '' })}>
                        <Pencil className="mr-1 h-3 w-3" /> Edit
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
      <p className="text-xs text-muted-foreground">Menampilkan {items.length} pemetaan.</p>

      <Dialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader><DialogTitle>Edit Pemetaan Test</DialogTitle></DialogHeader>
          {editing && (
            <div className="space-y-3">
              <div>
                <Label className="text-xs">Nama Test LIS</Label>
                <Input value={editing.lis_name || ''} disabled className="mt-1" />
              </div>
              <div>
                <Label className="text-xs">Nama Reagen Monitoring</Label>
                <Input
                  list="reagen-names-list"
                  data-testid="mapping-edit-reagen"
                  value={editing.reagen_name}
                  onChange={(e) => setEditing({ ...editing, reagen_name: e.target.value })}
                  className="mt-1"
                  placeholder="Ketik / pilih nama reagen"
                />
                <datalist id="reagen-names-list">
                  {reagenNames.map((n) => <option key={n} value={n} />)}
                </datalist>
              </div>
              <div>
                <Label className="text-xs">Status</Label>
                <Select value={editing.status} onValueChange={(v) => setEditing({ ...editing, status: v })}>
                  <SelectTrigger className="mt-1" data-testid="mapping-edit-status"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="OK">OK</SelectItem>
                    <SelectItem value="TIDAK ADA">TIDAK ADA</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditing(null)}>Batal</Button>
            <Button onClick={save} disabled={saving} data-testid="mapping-save-button">{saving ? 'Menyimpan...' : 'Simpan'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function RawTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('2026-07');
  const [sources, setSources] = useState([]);

  const load = () => {
    setLoading(true);
    Promise.all([api.lisRaw(period, 300, 0), api.lisSourceFiles(period)])
      .then(([raw, sf]) => { setData(raw); setSources(sf); })
      .finally(() => setLoading(false));
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [period]);

  const removeSource = async (sf) => {
    if (!window.confirm(`Hapus semua data LIS dari file "${sf}"? Pemakaian harian dari file ini juga akan dihapus.`)) return;
    try {
      const res = await api.deleteLisSourceFile(sf);
      toast.success(`File "${sf}" dihapus (${res.lis_raw_dihapus} data mentah, ${res.pemakaian_dihapus} pemakaian)`);
      load();
    } catch (e) {
      toast.error('Gagal menghapus source file');
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">Periode:</span>
        <Select value={period} onValueChange={setPeriod}>
          <SelectTrigger className="h-9 w-[150px]" data-testid="lis-period-filter"><SelectValue /></SelectTrigger>
          <SelectContent>
            {(data?.periods || ['2026-07', '2026-08']).map((p) => (
              <SelectItem key={p} value={p}>{p}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <span className="text-xs text-muted-foreground">Total {data?.total ?? 0} baris (menampilkan maks 300)</span>
      </div>

      {/* Source file management */}
      <Card className="p-4" data-testid="source-file-manager">
        <div className="mb-2 flex items-center gap-2 text-sm font-semibold"><FileX className="h-4 w-4 text-primary" /> Kelola Source File ({sources.length})</div>
        {sources.length === 0 ? (
          <p className="text-xs text-muted-foreground">Belum ada source file untuk periode ini.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {sources.map((s) => (
              <div key={s.source_file} className="flex items-center gap-2 rounded-md border bg-muted/30 py-1 pl-3 pr-1 text-xs" data-testid={`source-file-item-${s.source_file}`}>
                <span className="font-medium">{s.source_file}</span>
                <Badge variant="secondary" className="text-[10px]">{s.tests} test</Badge>
                <button
                  onClick={() => removeSource(s.source_file)}
                  data-testid={`source-file-delete-${s.source_file}`}
                  className="inline-flex h-6 w-6 items-center justify-center rounded hover:bg-destructive/10"
                  title="Hapus source file ini"
                >
                  <Trash2 className="h-3.5 w-3.5 text-destructive" />
                </button>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card className="p-0">
        {loading ? (
          <div className="p-4 space-y-2">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}</div>
        ) : (data?.items || []).length === 0 ? (
          <div className="p-10 text-center text-sm text-muted-foreground" data-testid="lis-raw-empty">Tidak ada data LIS mentah untuk periode ini.</div>
        ) : (
          <div className="overflow-auto" style={{ maxHeight: 'calc(100vh - 400px)' }}>
            <table className="w-full text-sm" data-testid="lis-raw-table">
              <thead className="sticky top-0 bg-card">
                <tr className="text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="px-4 py-2 text-left">Grup</th>
                  <th className="px-4 py-2 text-left">Nama Test</th>
                  <th className="px-4 py-2 text-right">Total</th>
                  <th className="px-4 py-2 text-left">Source File</th>
                </tr>
              </thead>
              <tbody>
                {(data?.items || []).map((r, i) => (
                  <tr key={i} className="border-t hover:bg-muted/40">
                    <td className="px-4 py-2 text-xs text-muted-foreground">{r.grup || '—'}</td>
                    <td className="px-4 py-2">{r.nama_test}</td>
                    <td className="num px-4 py-2 text-right font-medium">{fmtNum(r.total)}</td>
                    <td className="px-4 py-2 text-xs text-muted-foreground">{r.source_file || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

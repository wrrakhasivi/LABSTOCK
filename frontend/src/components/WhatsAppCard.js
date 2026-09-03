import React, { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { MessageCircle, Send, ExternalLink, Eye, EyeOff } from 'lucide-react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { api } from '../lib/api';
import { useAuth } from '../lib/auth';

export const WhatsAppCard = ({ year, month }) => {
  const { isKoordinator } = useAuth();
  const [prev, setPrev] = useState(null);
  const [jadwal, setJadwal] = useState(null);
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);

  const load = () => api.waPreview(year, month).then(setPrev).catch(() => setPrev(null));
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [year, month]);
  useEffect(() => { api.waJadwal().then(setJadwal).catch(() => setJadwal(null)); }, []);

  const send = async () => {
    setBusy(true);
    try {
      const res = await api.waSend(year, month);
      toast.success(res.mode === 'template'
        ? `Terkirim sebagai template (${res.note})`
        : `Notifikasi WhatsApp terkirim: ${res.critical} kritis, ${res.warning} waspada`);
      load();
      api.waJadwal().then(setJadwal).catch(() => {});
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Gagal mengirim WhatsApp');
    } finally { setBusy(false); }
  };

  const last = prev?.last_sent;
  return (
    <Card className="p-4" data-testid="whatsapp-card">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <MessageCircle className="h-4 w-4 text-emerald-600" /> Notifikasi WhatsApp
          <span className="text-xs font-normal text-muted-foreground" data-testid="whatsapp-recipient">→ {prev?.recipient || '+6285876806380'}</span>
        </div>
        <div className="flex items-center gap-2">
          <Badge className="bg-red-600 text-white" data-testid="whatsapp-critical-count">Kritis {prev?.critical ?? 0}</Badge>
          <Badge className="bg-amber-500 text-white" data-testid="whatsapp-warning-count">Waspada {prev?.warning ?? 0}</Badge>
          {prev && (
            <Badge variant={prev.configured ? 'default' : 'secondary'} data-testid="whatsapp-config-status">
              {prev.configured ? 'API aktif' : 'API belum dikonfigurasi'}
            </Badge>
          )}
        </div>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <Button size="sm" onClick={send} disabled={busy || !prev?.configured || !isKoordinator} data-testid="whatsapp-send-button"
          title={!isKoordinator ? 'Hanya Koordinator yang dapat mengirim notifikasi' : (prev?.configured ? 'Kirim via Meta WhatsApp Cloud API' : 'Isi WHATSAPP_ACCESS_TOKEN & WHATSAPP_PHONE_NUMBER_ID di backend/.env')}>
          <Send className="mr-1.5 h-3.5 w-3.5" /> {busy ? 'Mengirim...' : 'Kirim via API'}
        </Button>
        {prev?.wa_me && (
          <Button size="sm" variant="outline" asChild data-testid="whatsapp-wame-button">
            <a href={prev.wa_me} target="_blank" rel="noreferrer">
              <ExternalLink className="mr-1.5 h-3.5 w-3.5" /> Buka di WhatsApp
            </a>
          </Button>
        )}
        <Button size="sm" variant="ghost" onClick={() => setShow((s) => !s)} data-testid="whatsapp-preview-toggle">
          {show ? <EyeOff className="mr-1.5 h-3.5 w-3.5" /> : <Eye className="mr-1.5 h-3.5 w-3.5" />} {show ? 'Tutup pesan' : 'Lihat pesan'}
        </Button>
        {last && (
          <span className="text-xs text-muted-foreground" data-testid="whatsapp-last-sent">
            Terakhir: {new Date(last.created_at).toLocaleString('id-ID')} · {last.ok ? 'berhasil' : 'gagal'}{last.auto ? ' (otomatis)' : ''}
          </span>
        )}
      </div>
      {jadwal?.enabled && (
        <p className="mt-2 text-xs text-muted-foreground" data-testid="whatsapp-schedule-info">
          Terjadwal otomatis setiap hari pukul <b>{jadwal.jam} WIB</b>
          {jadwal.sudah_terkirim_hari_ini ? ' · sudah terkirim hari ini' : ''}.
        </p>
      )}
      {!prev?.configured && prev && (
        <p className="mt-2 text-xs text-muted-foreground">
          Pengiriman otomatis butuh <b>WHATSAPP_ACCESS_TOKEN</b> dan <b>WHATSAPP_PHONE_NUMBER_ID</b> (Meta for Developers → WhatsApp → API Setup) di <code>backend/.env</code>.
          Sementara itu gunakan tombol <b>Buka di WhatsApp</b> untuk mengirim pesan yang sudah terisi.
        </p>
      )}
      {show && prev?.message && (
        <pre className="mt-3 whitespace-pre-wrap rounded-md border bg-muted/40 p-3 text-xs" data-testid="whatsapp-message-preview">{prev.message}</pre>
      )}
    </Card>
  );
};

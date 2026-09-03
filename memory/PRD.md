# LabStock – Pemantauan Stok Reagen Laboratorium

## Problem Statement
Sistem monitoring stok reagen lab: import file LIS (Excel), pemetaan test LIS → reagen, perhitungan otomatis
pemakaian harian (1-31), QC manual, Sisa Stok otomatis, status Kritis/Waspada/Aman.

## Arsitektur
- Frontend React (`/app/frontend/src/pages/PemantauanStok.js`, `DataLIS.js`), FastAPI (`/app/backend/server.py`,
  `lis_import.py`, `calculations.py`, `seeder.py`), MongoDB.
- Kolom harian 1-31 dihitung dari `lis_raw` via `mapping_test` (status OK). Bukan dari `pemakaian_harian`.
- Import LIS idempoten per `source_file` (stem nama file).

## Format LIS yang didukung (`lis_import.py`)
1. Transaksi: kolom `Nama Test`, `Tanggal`, `Jumlah` per baris.
2. Matriks 1 baris header: `Grup | Nama Test | 1..31`.
3. Matriks 2 baris header (format LIS_260831 user): baris 1 `Grup | Nama Test | Tanggal (merged) | Total`,
   baris 2 angka hari 1..31. (Fix Juni 2026)
4. Satu tanggal dari nama file `LIS_YYMMDD` + kolom Jumlah/Total.

## Selesai
- Import saldo awal Agustus 2026, filter reagen status mapping OK, QC manual, Sisa Stok otomatis, CSS kolom harian.
- Fix bug LIS import: kolom Tanggal per baris & header 2 baris (hari 1-31 di baris ke-2).
- Sinkronisasi Pemetaan Test → Master Reagen (`_sync_master_reagen` di server.py): ubah "Nama Reagen Monitoring"
  otomatis rename master reagen (bila hanya dipakai 1 pemetaan), atau tautkan ke master yang sudah ada, atau buat
  master baru. Status otomatis OK bila nama diisi, TIDAK ADA bila kosong. Pemantauan Stok ikut nama baru.

- Dukungan file `.xls` (xlrd) di import LIS; endpoint & input file menerima .xlsx/.xlsm/.xls.
- Periode Bulan Baru: `POST /api/monitoring/periode-baru` {year, month} → buat bulan berikutnya (Des → Jan tahun
  berikutnya), saldo_awal = sisa_stock bulan ini. Tombol + dialog konfirmasi di Pemantauan Stok, otomatis pindah
  ke periode baru (PeriodContext.refreshPeriods).

- Notifikasi WhatsApp (Meta Cloud API, `backend/whatsapp.py`): `GET /api/notifikasi/whatsapp/preview`,
  `POST /api/notifikasi/whatsapp`. Kartu di Dashboard: Kirim via API (aktif bila env terisi), tombol wa.me fallback,
  pratinjau pesan. ENV: WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_API_VERSION,
  WHATSAPP_RECIPIENT_NUMBER=+6285876806380. **Token & Phone Number ID BELUM DIISI oleh user.** Fallback template
  hello_world bila teks ditolak (di luar jendela 24 jam). Log kirim di import_log (type 'whatsapp').
- Ekspor Excel (`backend/export_excel.py`, `GET /api/monitoring/export`): kolom harian 1-31, warna status per baris.
- Hapus Periode: `GET /api/monitoring/periode-info`, `DELETE /api/monitoring/periode?hapus_lis=` + dialog konfirmasi
  (komponen `frontend/src/components/PeriodActions.js`).
- Kolom harian dipersempit (`index.css` `.ls-day-col`), "Sorot Hari Ini" (highlight tanggal aktif) di PemantauanStok.js.
- Pemetaan Test persisten ke `seed/seed_data.json` (`seed_store.py`: persist_mapping, persist_reagen_rename,
  persist_new_reagen, remove_mapping) + tombol "Tambah Pemetaan" (modal) di DataLIS.js.
- WhatsApp Meta Cloud API terkonfigurasi & teruji (token, phone_id, recipient di backend/.env). Error Meta #131030
  (nomor belum di allowed list mode test) ditangani → HTTP 424 + hint Indonesia.
- **(2026-09-03) Hapus Pemetaan**: `DELETE /api/mapping-tests/{id}` + tombol "Hapus" di setiap baris Pemetaan Test
  (DataLIS.js), hapus dari DB & seed_data.json.
- **(2026-09-03) Jadwal Otomatis WhatsApp**: `_wa_scheduler_loop` (asyncio task, server.py) cek setiap 60 detik,
  kirim otomatis sekali/hari pukul 07:00 WIB (Asia/Jakarta) via `_kirim_whatsapp_otomatis`, idempoten lewat
  `import_log` (type=whatsapp, auto=True, sent_date). `GET /api/notifikasi/whatsapp/jadwal` untuk info UI;
  WhatsAppCard menampilkan "Terjadwal otomatis setiap hari pukul 07:00 WIB".
- **(2026-09-03) Keterangan "sudah PRF"**: `whatsapp.py build_message()` menambahkan "(sudah PRF)" pada baris
  reagen Kritis/Waspada yang sudah punya PRF di periode berjalan (`row['prf']` non-empty).
- Tested: `testing_agent` iteration_2 – backend 6/6 pytest, frontend semua flow baru PASS.

## Backlog
- P1: WhatsApp Send History – daftar riwayat kirim (waktu, status, jumlah kritis) di Dashboard.
- P2: Login & Peran (Petugas vs Koordinator) – batasi Hapus Periode untuk Koordinator.
- P2: Dropdown pilih Master Reagen pada edit Pemetaan Test.

## Catatan
- Testing agent backend menghapus `lis_raw`; setelah pakai testing agent, jalankan reseed (`POST /api/admin/reseed`).

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

## Backlog
- P1: Halaman Notifikasi/Dashboard (daftar reagen Kritis & Waspada saat aplikasi dibuka).
- P2: Login & Peran (Petugas vs Koordinator).
- P2: Dropdown pilih Master Reagen pada edit Pemetaan Test.

## Catatan
- Testing agent backend menghapus `lis_raw`; setelah pakai testing agent, jalankan reseed (`POST /api/admin/reseed`).

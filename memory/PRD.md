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

- **(2026-09-03) Login & Peran (Petugas vs Koordinator)**: JWT auth (`backend/auth.py`, PyJWT+bcrypt).
  Seluruh app terkunci di belakang login (`frontend/src/lib/auth.js` AuthContext, `App.js` Gate, `pages/Login.js`).
  Petugas = lihat saja (semua GET); Koordinator = akses penuh (semua POST/PUT/DELETE, via
  `Depends(auth.require_koordinator)` di server.py). Token Bearer disimpan di sessionStorage (hilang saat
  browser ditutup). UI menyembunyikan/disable semua tombol Tambah/Edit/Hapus untuk Petugas di: PemantauanStok
  (saldo/QC edit, Saldo Awal Otomatis, Periode Baru, Hapus Periode), MasterReagen (Edit), DataLIS (Import,
  Tambah/Edit/Hapus Pemetaan, hapus source file), PRF (Tambah/Terima/Hapus), Penerimaan (Terima), WhatsAppCard
  (Kirim via API). Akun tetap: kalgen/kalgen (petugas), raihan/rakhasivi123 (koordinator) — lihat
  `/app/memory/test_credentials.md`. Tested: testing_agent iteration_3 – backend 25/25 pytest, frontend semua
  RBAC flow PASS.

- **(2026-09-03) Bug Fix: Periode default setelah login**: `PeriodProvider` (frontend/src/lib/period.js) sebelumnya
  override year/month ke periode terbaru di DB (`periods[0]`, bisa jadi Januari 2027 sisa testing), bukan tanggal
  sistem sebenarnya. Fix: default year/month langsung dari `new Date()`, tidak lagi ditimpa oleh data DB.
  `AppShell.js` PeriodSelector year dropdown juga diperbaiki agar selalu menyertakan tahun berjalan meski belum
  ada data stock_period untuk tahun itu. Tested: testing_agent iteration_4 – frontend 100% PASS (verifikasi ulang
  setelah logout/login, ganti bulan, KPI dashboard).

- **(2026-09-03) Ganti Password & Kelola Pengguna**: `POST /api/auth/change-password` (self-service, wajib
  password lama, semua role) di `ChangePasswordDialog.js` (ikon kunci di topbar). Halaman baru `/pengguna`
  (`Pengguna.js`, khusus Koordinator, nav disembunyikan utk Petugas + akses ditolak bila diakses langsung):
  `GET/POST /api/users`, `DELETE /api/users/{username}` — Koordinator bisa lihat daftar akun, buat akun baru
  (role Petugas/Koordinator bebas dipilih), hapus akun (tidak bisa hapus diri sendiri / satu-satunya Koordinator).
  Tested: testing_agent iteration_5 – backend 22/22 pytest, frontend 100% PASS.

- **(2026-09-03) Security Audit + Fixes**: `security_audit_agent` menemukan 1 CRITICAL + 3 MEDIUM, user approved
  fix semua 4: (1) `auth.seed_accounts()` tidak lagi menimpa password akun yang sudah ada saat restart (bug ini
  bisa merusak fitur Ganti Password untuk kalgen/raihan); (2) token JWT kini membawa klaim `tv` (token_version)
  yang divalidasi ulang ke DB di `get_current_user` — password diubah/akun dihapus langsung 401 tanpa menunggu
  token expired 12 jam; `change_password` melakukan `$inc token_version` (invalidasi semua sesi lama akun itu),
  frontend auto-logout setelah ganti password sendiri; (3) `GET /api/reagen?query=` kini `re.escape()` mencegah
  ReDoS; (4) `POST /api/lis/import` dibatasi `MAX_LIS_FILES=50` & `MAX_LIS_FILE_SIZE=10MB`/file. Tested:
  testing_agent iteration_6 – backend 11/11 pytest (`tests/test_security_fixes.py`), frontend 100% PASS.

- **(2026-09-03) Dark Mode + Toggle**: `.dark` CSS variable block ditambahkan di `index.css` (background,
  foreground, card, primary, dst.). `lib/theme.js` (ThemeProvider, localStorage `ls_theme`, hormati
  prefers-color-scheme) + `components/ThemeToggle.js` (ikon Matahari/Bulan) — tombol tersedia di halaman Login
  (pojok kanan atas) dan topbar semua halaman terautentikasi. Preferensi tema persisten lintas reload &
  logout/login (localStorage, bukan sessionStorage). Perbaikan kontras: hero banner Dashboard & AnalisisExcel
  (gradient gelap di dark mode), badge "Perlu Cek", pill role Petugas/Koordinator, input edit Saldo Awal/QC.
  Tested: testing_agent iteration_7 – frontend 100% PASS, tidak ada regresi mode terang.

- **(2026-09-03) Auto-Hapus File Mentah Excel LIS**: File Excel LIS TIDAK pernah disimpan di disk (hanya
  diparse in-memory), jadi fitur ini menghapus baris arsip `lis_raw` (bukan `pemakaian_harian`/`stock_period`
  yang sudah terintegrasi ke Pemantauan Stok) setelah periode retensi sejak `uploaded_at`. Halaman baru
  `/pengaturan` (koordinator-only, `Pengaturan.js`) dengan pilihan 3/7/30 hari (`GET/PUT /api/settings`,
  `settings_col`). Backend: `_backfill_lis_raw_uploaded_at()` sekali saat startup (data lama tidak langsung
  terhapus), `_lis_retention_loop()` bersihkan setiap 1 jam, log ke `import_log` (type=`lis_cleanup`).
  **Tema default Light**: `lib/theme.js` tidak lagi ikuti `prefers-color-scheme` OS — default selalu Light
  saat belum ada preferensi tersimpan. Tested: testing_agent iteration_8 – backend 17/17 pytest, frontend
  100% PASS.

## Backlog
- P1: WhatsApp Send History – daftar riwayat kirim (waktu, status, jumlah kritis) di Dashboard.
- P2: Dropdown pilih Master Reagen pada edit Pemetaan Test.
- P2: /app/backend/tests/test_new_features.py (pra-auth) perlu token koordinator agar lolos lagi.

## Catatan
- Testing agent backend menghapus `lis_raw`; setelah pakai testing agent, jalankan reseed (`POST /api/admin/reseed`).

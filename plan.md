# LabStock – Sistem Pemantauan Stok Reagen Laboratorium PK (Tahap 1) — plan.md

## STATUS: ✅ TAHAP 1 SELESAI (diverifikasi Testing Agent 100% — backend 13/13, frontend semua fitur, 0 issue)
- Backend: model MongoDB (9 entitas), seeder dari Excel (117 reagen, 200 stock_period, 2447 pemakaian harian, 247 mapping, 1113 LIS, 64 PRF, 51 penerimaan), API dasar lengkap.
- Frontend: AppShell + 7 halaman (Dashboard, Pemantauan Stok tabel 1-31 + status warna, Master Reagen + edit, Data LIS raw+mapping, PRF, Penerimaan, Analisis Struktur Excel).
- Logika bisnis (total pemakaian, sisa stok, status warna KRITIS/WASPADA/AMAN/PERLU CEK) sesuai Excel.
- Selanjutnya (Fase 2+): input pemakaian harian manual, form PRF & penerimaan, manajemen periode otomatis, integrasi LIS, auth.


## 1) Objectives
- Mengubah sistem Excel **PEMANTAUAN STOCK REAGEN LAB PK** menjadi aplikasi web full-stack (FastAPI + MongoDB + React + shadcn/ui) **tanpa menghilangkan logika bisnis & konsep kolom**.
- Menyimpan data di database berbasis **tanggal** (bukan kolom 1–31 di DB), tetapi **menampilkan kembali** format monitoring harian 1–31 seperti Excel.
- Menyediakan fondasi Tahap 1 sesuai output: struktur project, skema DB normal, backend+API dasar, halaman awal + placeholder menu, dan halaman dokumentasi **ringkasan analisis Excel**.
- Seed data nyata dari Excel (via `seed_data.json`) untuk memvalidasi alur end-to-end tanpa mock.

## 2) Implementation Steps

### Phase 1 — Core Workflow (No separate POC required)
**Core flow:** pilih bulan → tampilkan tabel monitoring reagen (kolom harian 1–31) → hitung total pemakaian, stok masuk, sisa stok, buffer, dan status warna konsisten dengan Excel.

User stories:
1. Sebagai petugas lab, saya ingin memilih bulan/tahun dan langsung melihat pemantauan stok reagen seperti di Excel.
2. Sebagai petugas lab, saya ingin kolom harian 1–31 tampil seperti Excel agar mudah membandingkan pemakaian harian.
3. Sebagai petugas lab, saya ingin sistem otomatis menghitung total pemakaian, sisa stok, dan saldo akhir agar tidak salah hitung manual.
4. Sebagai petugas lab, saya ingin melihat status warna (aman/mendekati buffer/dibawah buffer) agar bisa cepat mengambil tindakan.
5. Sebagai koordinator, saya ingin melihat data PRF & penerimaan terkait reagen agar bisa melacak proses pemesanan.

Tasks:
- Tetapkan model perhitungan server-side sesuai Excel:
  - `total_pemakaian = sum(pemakaian_harian 1..31) + qc`
  - `stok_masuk = sum(order_qty dari penerimaan)`
  - `sisa_stock = saldo_awal - total_pemakaian + stok_masuk`
  - `status`: MERAH jika `sisa<=buffer`, KUNING jika `buffer+1..buffer+10`, selain itu HIJAU.
- Putuskan aturan data rusak `#REF!`: simpan sebagai `null` saat seed dan biarkan sistem menghitung bila mungkin.

Deliverable phase: spesifikasi core + fungsi kalkulasi teruji lewat unit test sederhana (tanpa integrasi eksternal).

---

### Phase 2 — V1 App Development (Tahap 1 deliverables)
User stories:
1. Sebagai user, saya ingin melihat halaman awal yang menjelaskan fungsi LabStock dan shortcut ke menu utama.
2. Sebagai user, saya ingin membuka halaman **Pemantauan Stok** dan melihat tabel bulanan (rekonstruksi 1–31) dari database.
3. Sebagai user, saya ingin membuka **Master Reagen** untuk melihat daftar reagen dan atribut penting (qty/kit, avg, buffer, satuan).
4. Sebagai user, saya ingin membuka **Data LIS** dan melihat data LIS mentah + mapping test (read-only) agar tahu cakupan mapping.
5. Sebagai user, saya ingin membuka halaman **PRF** dan **Penerimaan** (placeholder + list read-only dari seed) agar alur bisnis terlihat.

Tasks (build in minimal bulk steps):
1. **Project structure**
   - Backend FastAPI: `app/main.py`, `app/db.py`, `app/models/*`, `app/routes/*`, `app/services/calculation.py`, `app/seed/seed_from_json.py`.
   - Frontend React: layout + routing + shadcn/ui base.

2. **Database schema (MongoDB, date-based)**
   - `master_reagen`:
     - `_id`, `nama_reagen` (unique), `item_code` (nullable), `qty_per_kit`, `avg_2022`, `avg_2023`, `buffer_stock`, `satuan`, `aktif`.
   - `stock_period` (bulanan):
     - `_id`, `reagen_id`, `year`, `month`, `saldo_awal`, `qc`, `buffer_override` (nullable), `created_at`.
   - `pemakaian_harian`:
     - `_id`, `reagen_id`, `date` (YYYY-MM-DD), `jumlah`, `source` (PQ/LIS/manual), `created_at`.
   - `prf`:
     - `_id`, `reagen_id`, `tanggal_pr`, `reagent_no` (1/2), `kits`, `status` (open/received/cancelled), `note`.
   - `penerimaan`:
     - `_id`, `reagen_id`, `tanggal_terima`, `reagent_no`, `kits`, `qty` (computed = qty_per_kit * kits), `note`.
   - `mapping_test`:
     - `_id`, `lis_name`, `reagen_name` (nullable), `status` (OK/TIDAK ADA).
   - `lis_raw` (read-only seed for Tahap 1):
     - `_id`, `period` (YYYY-MM), `grup`, `nama_test`, `date`, `jumlah`, `source_file`.
   - `import_log`:
     - `_id`, `type` (seed/manual/import), `filename`, `period`, `inserted`, `errors`, `created_at`.
   - `users` (disiapkan untuk fase berikutnya, belum dipakai):
     - `_id`, `email`, `password_hash`, `role`, `active`.

3. **Seeding**
   - Import `seed_data.json`:
     - upsert `master_reagen` dari Juli/Aug.
     - create `stock_period` untuk 2026-07 dan 2026-08 (saldo_awal dari seed; null jika `#REF!`).
     - create `pemakaian_harian` dari PQ_Juli/PQ_Aug: map day 1–31 menjadi tanggal aktual.
     - create `mapping_test` dari Mapping_Test.
     - log ke `import_log`.

4. **Backend API (prefix `/api`)**
   - `GET /api/health`
   - `GET /api/meta/excel-summary` (ringkasan struktur Excel & aturan warna)
   - Master Reagen:
     - `GET /api/reagen?query=`
     - `POST /api/reagen` (basic)
     - `PUT /api/reagen/{id}`
   - Monitoring bulanan (core):
     - `GET /api/monitoring?year=2026&month=7`
       - Return: list reagen + kolom `hari[1..31]` (rekonstruksi), `qc`, `total_pemakaian`, `saldo_awal`, `stok_masuk`, `sisa_stock`, `buffer_stock`, `status_color`, `prf`, `penerimaan`.
   - Mapping/LIS (read-only tahap 1):
     - `GET /api/mapping-tests?status=`
     - `GET /api/lis/raw?period=2026-07`
   - PRF & Penerimaan (list/create minimal, boleh read-only jika belum ada input UI):
     - `GET /api/prf?year=&month=`
     - `GET /api/penerimaan?year=&month=`

5. **Frontend (React + shadcn/ui, Bahasa Indonesia)**
   - Navigation sidebar/topbar: Dashboard, Pemantauan Stok, Master Reagen, Data LIS, PRF, Penerimaan, Analisis Excel.
   - Halaman:
     - Landing/Dashboard (placeholder ringkas + link cepat)
     - Pemantauan Stok: pilih bulan/tahun, tabel 1–31 + kolom QC/Total/Sisa/Buffer/Status; warna sesuai aturan.
     - Master Reagen: tabel + edit sederhana.
     - Data LIS: tab LIS Raw (read-only) + Mapping Test (filter OK/TIDAK ADA).
     - PRF: placeholder list.
     - Penerimaan: placeholder list.
     - Analisis Struktur Excel: tampilkan ringkasan dari endpoint `/meta/excel-summary`.

6. **Testing & stabilization (end-to-end)**
   - Jalankan seed pada startup/dev command.
   - Tes API utama: monitoring bulan Juli & Agustus, mapping list, reagen list.
   - Tes UI: navigasi antar halaman, load tabel monitoring, status warna muncul, error state (tanpa data period).

---

### Phase 3 — Next Features (NOT in Tahap 1, only plan)
User stories:
1. Sebagai petugas lab, saya ingin input/edit pemakaian harian per tanggal agar bisa koreksi data.
2. Sebagai petugas lab, saya ingin membuat PRF dari halaman monitoring ketika stok mendekati buffer.
3. Sebagai petugas lab, saya ingin input penerimaan barang dan otomatis menambah stok masuk.
4. Sebagai koordinator, saya ingin alarm/notifikasi daftar reagen merah/kuning.
5. Sebagai admin, saya ingin login + role agar akses fitur terbatas.

Planned tasks:
- Form input pemakaian harian, PRF, penerimaan + audit trail.
- Manajemen periode (buat bulan baru otomatis: saldo_awal = sisa bulan sebelumnya).
- Import LIS file + mapping pipeline (tetap date-based).
- Auth (users, JWT) setelah core stabil.

## 3) Next Actions (immediate)
1. Buat skema MongoDB + model Pydantic + koleksi indeks (unique `nama_reagen`).
2. Implement seeder dari `seed_data.json` + `import_log`.
3. Implement service kalkulasi monitoring (rekonstruksi day 1–31 dari `pemakaian_harian`).
4. Implement endpoint `/api/monitoring` dan `/api/meta/excel-summary`.
5. Buat frontend routing + halaman Pemantauan Stok (tabel) + halaman Analisis Excel.
6. End-to-end test dan perbaiki hingga app stabil.

## 4) Success Criteria
- Aplikasi berjalan tanpa error (backend+frontend) dan data tersimpan di MongoDB.
- Seed sukses: master reagen, pemakaian harian (date-based), mapping test terisi.
- Halaman **Pemantauan Stok** menampilkan kolom 1–31 (rekonstruksi) + QC/Total/Sisa/Buffer + status warna sesuai aturan Excel.
- Halaman placeholder lain tampil dan tidak crash; Data LIS & Mapping bisa dibuka (read-only).
- Halaman **Analisis Struktur Excel** menampilkan ringkasan kolom & rumus inti (dari API/dok) sehingga blueprint Excel tetap transparan.

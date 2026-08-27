"""Documented analysis of the source Excel workbook (blueprint).

This is surfaced via GET /api/meta/excel-summary and rendered on the
'Analisis Struktur Excel' page so the Excel blueprint stays transparent.
"""

EXCEL_SUMMARY = {
    "file": "PEMANTAUAN STOCK REAGEN LAB PK 2026.xlsx",
    "ringkasan": (
        "Workbook Excel yang dipakai untuk memantau stok reagen Laboratorium "
        "Patologi Klinik. Setiap bulan memiliki satu sheet pemantauan (mis. "
        "Juli2026, Aug2026). LabStock menggantinya dengan penyimpanan berbasis "
        "tanggal sehingga bisa dipakai lintas bulan/tahun tanpa membuat sheet baru."
    ),
    "sheets": [
        {"nama": "Juli2026 / Aug2026", "peran": "Sheet PEMANTAUAN STOK bulanan (utama)",
         "keterangan": "Satu baris per reagen. Kolom harian 1-31, QC, total pemakaian, sisa stok, buffer, PRF & penerimaan."},
        {"nama": "PQ_Juli / PQ_Aug / PQ_Harian", "peran": "Sumber Pemakaian Harian",
         "keterangan": "Jumlah pemakaian per test per hari (kolom 1-31 + Total). Ditarik ke sheet bulanan via INDEX/MATCH."},
        {"nama": "LIS_Juli / LIS_Aug / LIS_Histori", "peran": "Data mentah LIS",
         "keterangan": "Ekspor dari LIS: Grup, Nama Test, jumlah per hari 1-31, Total, SourceFile."},
        {"nama": "Mapping_Test", "peran": "Pemetaan nama test",
         "keterangan": "Menghubungkan Nama Test LIS -> Nama Reagen Monitoring, dengan status OK / TIDAK ADA."},
    ],
    "kolom_monitoring": [
        {"kolom": "REAGEN (C)", "arti": "Nama reagen (identitas utama)."},
        {"kolom": "Qty/kit (D)", "arti": "Jumlah tes/pcs per kit reagen."},
        {"kolom": "AVG Sampel 2022 (E)", "arti": "Rata-rata sampel per bulan tahun 2022."},
        {"kolom": "AVG Sampel 2023 (F)", "arti": "Rata-rata sampel per bulan tahun 2023."},
        {"kolom": "Saldo Awal (G)", "arti": "Stok awal bulan = sisa stok bulan sebelumnya (berantai antar bulan)."},
        {"kolom": "Hari 1-31 (H..AL)", "arti": "Pemakaian harian, ditarik dari sheet PQ."},
        {"kolom": "QC (AM)", "arti": "Pemakaian untuk Quality Control."},
        {"kolom": "Total Pemakaian (AN)", "arti": "SUM(pemakaian harian) + QC."},
        {"kolom": "Sisa Stock (AO)", "arti": "(Saldo Awal - Total Pemakaian) + Stok Masuk."},
        {"kolom": "Buffer Stock (AP)", "arti": "Ambang minimum. Definisi: 30% tambahan dari rata-rata sampel per bulan setahun."},
        {"kolom": "Satuan (AQ)", "arti": "Satuan stok (mis. Pcs)."},
        {"kolom": "Tanggal PR 1 & 2 (AR, AT)", "arti": "Tanggal Purchase Request (PRF) reagent ke-1 & ke-2, dengan jumlah Kit (AS, AU)."},
        {"kolom": "Tanggal Terima 1 & 2 (AV, AW)", "arti": "Tanggal penerimaan barang reagent ke-1 & ke-2."},
        {"kolom": "Penambahan Stok (AX, AY, AZ)", "arti": "Order1 = IF(terima1 kosong,0,Qty/kit*Kit1); Order2 sama; Jumlah = Order1 + Order2."},
        {"kolom": "Saldo Akhir (BA)", "arti": "(Saldo Awal - Total Pemakaian) + Stok Masuk (sama dengan Sisa Stock)."},
    ],
    "rumus": [
        {"nama": "Total Pemakaian", "rumus": "SUM(pemakaian_harian[1..31]) + QC"},
        {"nama": "Stok Masuk", "rumus": "(Qty/kit * Kit1 jika diterima) + (Qty/kit * Kit2 jika diterima)"},
        {"nama": "Sisa Stok / Saldo Akhir", "rumus": "(Saldo Awal - Total Pemakaian) + Stok Masuk"},
        {"nama": "Saldo Awal bulan berikutnya", "rumus": "= Sisa Stok bulan sebelumnya (berantai)"},
        {"nama": "Buffer Stock", "rumus": "30% tambahan dari rata-rata sampel per bulan dalam setahun"},
    ],
    "status_warna": [
        {"status": "KRITIS", "warna": "Merah", "aturan": "Sisa Stok <= Buffer Stock", "tindakan": "Di bawah buffer, CITO untuk pemesanan barang."},
        {"status": "WASPADA", "warna": "Kuning", "aturan": "Buffer+1 <= Sisa Stok <= Buffer+10", "tindakan": "Sudah mendekati buffer, mulai dipesan barangnya."},
        {"status": "AMAN", "warna": "Hijau", "aturan": "Sisa Stok > Buffer+10", "tindakan": "Stok aman."},
    ],
    "status_prf": [
        {"kondisi": "PR dibuat & belum diterima, 3-10 hari", "arti": "Peringatan: pantau penerimaan."},
        {"kondisi": "PR dibuat & belum diterima, > 10 hari", "arti": "Eskalasi: tindak lanjut pemesanan."},
        {"kondisi": "Tanggal terima terisi", "arti": "Barang sudah diterima (selesai)."},
    ],
    "entitas_database": [
        "master_reagen", "stock_period (histori bulanan)", "pemakaian_harian (berbasis tanggal)",
        "stok_masuk / penerimaan", "prf", "mapping_test", "lis_raw", "import_log", "users",
    ],
    "catatan": (
        "Kolom tanggal 1-31 TIDAK disimpan sebagai 31 kolom database. Pemakaian disimpan "
        "per (reagen_id, tanggal, jumlah) lalu direkonstruksi menjadi kolom 1-31 di halaman "
        "Pemantauan Stok. Beberapa sel di Excel asli berisi #REF! (referensi rusak) dan "
        "diperlakukan sebagai kosong lalu dihitung ulang oleh sistem."
    ),
}

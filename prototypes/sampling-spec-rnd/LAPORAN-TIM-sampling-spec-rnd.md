# Laporan Internal Tim — Modul Sampling & Spec R&D
**Lukla Operations Engine · Dokumen Referensi Tim**  
Versi: 1.0.0 · Tanggal: Oktober 2026

---

## 1. Apa itu Modul Ini?

Modul **Sampling & Spec R&D** adalah sistem pencatatan dan analisis dua fungsi utama dalam proses produksi pabrik tekstil Lukla:

### ⏱ Time Study (Studi Waktu)
Pengukuran waktu siklus setiap proses manufaktur secara sistematis menggunakan metode sampling statistik. Data ini menjadi dasar penetapan **standar waktu kerja**, efisiensi lini, dan perhitungan upah satuan *(piece-rate)*.

### 📄 Spec Version (Versi Spesifikasi)
Pengelolaan versi dokumen spesifikasi teknis produk seperti toleransi jahitan, kualitas material, dan parameter proses. Setiap perubahan dicatat dengan **jejak audit lengkap** yang tidak dapat dihapus.

---

## 2. Posisi dalam Sistem Lukla

```
┌───────────────────────────────────────────────────────┐
│          INTI ENTRI GANDA YANG TIDAK DAPAT DIUBAH     │
│  ┌─────────────────────┐  ┌──────────────────────┐   │
│  │ Buku Besar Keuangan │  │ Inventaris Multi-    │   │
│  │ (COA, Debit, Kredit)│  │ Penyewa (Konsinyasi) │   │
│  └─────────────────────┘  └──────────────────────┘   │
└───────────────────────────────────────────────────────┘
                  ↓ Acara / Batasan Ketat
┌─────────────────┐  ┌─────────────────┐  ┌───────────┐
│ Sampling &      │  │ Eksekusi        │  │ QC & MES  │
│ Spec R&D ◄ ANDA │  │ Manufaktur      │  │           │
│ (Studi Waktu,   │  │ (Lini, Mandor)  │  │ (Lulus,   │
│  Versi Spec)    │  │                 │  │  Tolak)   │
└─────────────────┘  └─────────────────┘  └───────────┘
                  ↓ Penyelesaian Terverifikasi
          ┌──────────────────────────────┐
          │   Mesin Penggajian Dinamis   │
          │   (Tarif Per Unit, QC Pool)  │
          └──────────────────────────────┘
```

> **Catatan:** Diagram visual HTML tersedia di file `sampling-spec-rnd-architecture.html` di folder yang sama.

---

## 3. Kegunaan untuk Perusahaan Lukla

### 📊 Standarisasi Waktu Kerja
Data time study dari **30+ sampel per proses** digunakan untuk menetapkan standar waktu (normal time + allowance). Hasil ini menjadi acuan target produksi harian setiap operator dan dasar penilaian kinerja lini.

### 💰 Dasar Perhitungan Upah Piece-Rate
Waktu siklus rata-rata yang valid menjadi input untuk **Mesin Penggajian Dinamis**. Tanpa data time study yang akurat dan tervalidasi secara statistik, upah satuan tidak bisa dihitung secara adil dan transparan.

### 🔄 Kontrol Perubahan Spesifikasi
Setiap perubahan pada spesifikasi teknis (toleransi, material, langkah proses) direkam dengan:
- Tipe perubahan (MODIFICATION, ADDITION, REMOVAL, dll)
- Nilai lama dan nilai baru
- Alasan perubahan
- Nama pembuat perubahan

Tim QC dan produksi selalu menggunakan versi spesifikasi yang sama dan telah disetujui.

### ⚠️ Deteksi Drift Spesifikasi
Ketika hasil pengukuran menyimpang dari batas spesifikasi, sistem mencatat **drift** dengan tingkat keparahan:
- `low` — deviasi kecil, masih dalam toleransi
- `medium` — perlu perhatian, monitor ketat
- `high` — tindakan korektif segera diperlukan
- `critical` — hentikan produksi, eskalasi ke manajemen

Tim dapat melacak parameter mana yang paling sering menyimpang untuk tindakan preventif.

### ✅ Alur Persetujuan Formal
Versi spesifikasi melewati alur yang terkontrol:

```
Draf → Review → Disetujui → Aktif
```

Tidak ada spesifikasi yang diterapkan ke produksi tanpa **persetujuan resmi** dari pihak berwenang.

### 🔗 Integrasi dengan Modul Lain
- Data **studi waktu** → Mesin Penggajian (standar waktu untuk piece-rate)
- Data **spesifikasi aktif** → Modul QC & MES (validasi hasil produksi)
- Semua event → Buku Besar Keuangan (immutable double-entry)

---

## 4. Tujuan Teknis untuk Tim Pengembang

| Prinsip | Penjelasan |
|---|---|
| **Single Source of Truth** | Satu database untuk semua data waktu siklus dan spesifikasi. Tidak ada data duplikat di spreadsheet atau dokumen terpisah. |
| **Immutability & Audit Trail** | Setiap perubahan dicatat permanen. Data yang sudah disubmit tidak bisa dihapus, hanya bisa superseded atau archived. |
| **Multi-Tenant Ready** | Semua data diberi `tenant_id` sehingga satu deployment bisa melayani beberapa pabrik/divisi Lukla secara terpisah. |
| **API-First** | Semua fungsi tersedia via REST API sehingga modul ini bisa diintegrasikan oleh tim mobile, tim ERP, atau sistem eksternal. |
| **Statistical Validity** | Sistem menghitung mean, std dev, dan confidence interval otomatis untuk memastikan ukuran sampel cukup secara statistik. |

---

## 5. Referensi Endpoint API (24 Endpoints)

### ⏱ Time Study

| Method | Endpoint | Kegunaan |
|---|---|---|
| POST | `/studies/create` | Buat studi baru |
| POST | `/studies/{id}/start` | Mulai rekam sampel |
| POST | `/studies/{id}/add-sample` | Tambah satu sampel waktu siklus |
| POST | `/studies/{id}/pause` | Jeda pengambilan sampel |
| POST | `/studies/{id}/resume` | Lanjutkan setelah jeda |
| POST | `/studies/{id}/complete` | Finalisasi studi |
| GET | `/studies/{id}/data` | Ambil data lengkap studi |
| GET | `/studies/{id}/stats` | Ambil statistik (mean, std dev, dll) |

### 📄 Spec Version

| Method | Endpoint | Kegunaan |
|---|---|---|
| POST | `/specs/create` | Buat versi spec baru |
| POST | `/specs/{id}/record-change` | Catat perubahan parameter |
| POST | `/specs/{id}/record-drift` | Catat deviasi dari batas spec |
| POST | `/specs/{id}/resolve-drift/{drift_id}` | Tandai drift sudah ditangani |
| POST | `/specs/{id}/submit-review` | Submit ke reviewer |
| POST | `/specs/{id}/approve` | Setujui versi spec |
| POST | `/specs/{id}/activate` | Aktifkan untuk produksi |
| GET | `/specs/{id}/data` | Ambil data lengkap spec |
| GET | `/specs/{id}/drift-report` | Laporan drift summary |
| GET | `/specs/{id}/drift-analysis` | Analisis trend drift + risk score |
| GET | `/specs/{id}/change-history` | Riwayat perubahan parameter |

### 🔧 Utilitas

| Method | Endpoint | Kegunaan |
|---|---|---|
| GET | `/workflow/summary` | Ringkasan semua studi & spec per tenant |
| GET | `/health` | Health check backend |

> **Swagger Docs Interaktif:** `http://127.0.0.1:8009/docs`

---

## 6. Panduan Integrasi untuk Tim

### 📌 Untuk Tim Payroll (Integrasi Hilir)
Setelah time study berstatus `completed`, ambil data via:
```
GET /studies/{id}/stats
```
Response berisi `mean_cycle_time_ms` dan `std_dev`. Gunakan `mean_cycle_time_ms` sebagai **standard time** input ke engine upah piece-rate.

**Formula:**
```
Normal Time = mean_cycle_time_ms × performance_rating
Standard Time = Normal Time × (1 + allowance_percent / 100)
Piece Rate = hourly_wage / (3600000 / Standard Time)
```

### 📌 Untuk Tim QC & MES (Integrasi Hilir)
Ambil spesifikasi aktif via:
```
GET /specs/{id}/data
```
Validasi hasil produksi terhadap field `tolerances`. Jika ada deviasi, report ke:
```
POST /specs/{id}/record-drift
```
dengan parameter `severity` yang sesuai (`low` / `medium` / `high` / `critical`).

### 📌 Untuk Tim Frontend Lanjutan
Semua API sudah tersedia di:
```
frontend/sampling-spec-rnd/src/services/api.ts
```
TypeScript types lengkap di:
```
frontend/sampling-spec-rnd/src/types/index.ts
```
Import langsung:
```typescript
import * as api from '@/services/api';
import type { TimeStudy, SpecVersion } from '@/types';
```

---

## 7. Cara Menjalankan

### Backend
```powershell
cd backend\sampling-spec-rnd
.\venv\Scripts\activate
uvicorn src.main:app --reload --port 8009
```

### Frontend
```powershell
cd frontend\sampling-spec-rnd
npm run dev
# Buka: http://localhost:3009
```

### Environment Variables
Salin `.env.example` ke `.env` di masing-masing folder dan isi nilai yang sesuai.

---

## 8. Status Implementasi

| Komponen | Status |
|---|---|
| Backend API (24 endpoints) | ✅ Selesai |
| Frontend Time Study | ✅ Selesai |
| Frontend Spec Version | ✅ Selesai |
| Integrasi Frontend↔Backend | ✅ Selesai |
| TypeScript (0 errors) | ✅ Selesai |
| CORS konfigurasi | ✅ Selesai |
| Environment variables (.env) | ✅ Selesai |
| Database PostgreSQL | 🟡 Schema siap, koneksi perlu dikonfigurasi per environment |
| AWS Bedrock integration | 🟡 Credentials siap di .env, implementasi diserahkan ke tim |
| Authentication/Authorization | ⬜ Belum — diserahkan ke tim integrasi |

---

*Lukla Operations Engine · Modul Sampling & Spec R&D · v1.0.0*  
*Dokumen ini dibuat sebagai referensi tim dan tidak boleh didistribusikan ke luar organisasi.*

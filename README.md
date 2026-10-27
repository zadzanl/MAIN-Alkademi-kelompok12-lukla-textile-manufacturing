# Lukla - Textile Manufacturing Operations Platform

Lukla adalah platform operasi manufaktur tekstil yang menyatukan produksi, gudang, quality control, sampling, hingga payroll dalam satu aplikasi. Tim tidak perlu berpindah-pindah tool lagi.

**Bahasa:** Indonesia · [English](./README.en.md)

## Fitur Utama

- Dashboard operasional dan ringkasan aktivitas pabrik.
- AI Copilot untuk menjawab pertanyaan operasional dengan bahasa sehari-hari.
- Manajemen gudang, stok, dan transaksi inventory.
- Monitoring produksi dan pencatatan pekerjaan line sewing.
- Sampling, time study, spesifikasi, dan analisis quality control.
- Payroll berbasis piece-rate beserta kontrol finansialnya.
- Portal login untuk pengguna internal.

## Struktur Repository

| Folder/File | Keterangan |
| --- | --- |
| `backend/` | Lukla Operations Engine API utama (port 8000) |
| `prototypes/sampling-spec-rnd/backend/` | API prototype sampling dan operasi (port 8009) |
| `prototypes/sampling-spec-rnd/frontend/` | Aplikasi web React + Vite (port 3009) |
| `prototypes/uhuy-b2b-portal/` | Prototype portal B2B pendamping |
| `USER_GUIDE.md` | Panduan penggunaan aplikasi |

## Cara Menjalankan

### Prasyarat

- Python 3.11 atau versi Python yang kompatibel dengan `requirements.txt`.
- Node.js 20 atau lebih baru, beserta npm.
- Git.

Jalankan setiap service di terminal terpisah. Semua perintah di bawah ini dijalankan dari root repository, kecuali jika disebutkan direktori kerja lain.

### 1. Backend utama - port 8000

Pasang dependency backend satu kali:

```powershell
python -m pip install -r prototypes/sampling-spec-rnd/backend/requirements.txt
```

Jalankan API utama:

```powershell
python -m uvicorn backend.app.main:app --reload --port 8000
```

Jika berhasil, dokumentasi API dapat dibuka di `http://localhost:8000/docs`.

### 2. Backend prototype - port 8009

```powershell
Set-Location prototypes/sampling-spec-rnd/backend
python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8009
```

Jika berhasil, health check mengembalikan status sehat:

```powershell
Invoke-RestMethod http://localhost:8009/health
```

### 3. Frontend - port 3009

Buka terminal baru, lalu jalankan:

```powershell
Set-Location prototypes/sampling-spec-rnd/frontend
npm install
npm run dev
```

Jika berhasil, halaman login terbuka di `http://localhost:3009`.

Frontend menggunakan proxy Vite. Request `/api/v1` diteruskan ke backend port 8000, sedangkan `/api` dan AI Copilot diteruskan ke backend port 8009. Karena itu, jalankan ketiga service agar aplikasi berfungsi penuh.

## Kredensial Demo

- **Identifier:** `ADMIN-IT`
- **Password:** `Admin#12345`

Masukkan `ADMIN-IT` pada field login **identifier** di halaman `http://localhost:3009`.

## Panduan Pengguna

Buka [USER_GUIDE.md](./USER_GUIDE.md) untuk panduan lengkap seluruh fitur aplikasi.

## Catatan Proyek

Folder `frontend/` di root bukan aplikasi frontend utama, melainkan harness pengujian Playwright untuk design mock. Aplikasi demo yang dijalankan berada di `prototypes/sampling-spec-rnd/`.
# Lukla - Textile Manufacturing Operations Platform

Lukla adalah platform operasi manufaktur tekstil untuk membantu tim mengelola
proses produksi, gudang, quality control, sampling, dan payroll dalam satu
aplikasi. Proyek ini dibuat oleh **Kelompok 12** untuk **MAIN Alkademi Hackathon
2026**.

## Fitur Utama

- Dashboard operasional dan ringkasan aktivitas pabrik.
- AI Copilot untuk pertanyaan operasional dengan bahasa natural.
- Manajemen gudang, stok, dan transaksi inventory.
- Monitoring produksi dan pencatatan pekerjaan line sewing.
- Sampling, time study, spesifikasi, dan analisis quality control.
- Payroll berbasis piece-rate serta kontrol finansial terkait.
- Portal autentikasi pengguna internal.

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
- Node.js 20 atau lebih baru dan npm.
- Git.

Jalankan setiap service pada terminal terpisah. Semua perintah berikut dijalankan
dari root repository, kecuali jika direktori kerja disebutkan.

### 1. Backend utama - port 8000

Install dependency backend satu kali:

```powershell
python -m pip install -r prototypes/sampling-spec-rnd/backend/requirements.txt
```

Jalankan API utama:

```powershell
python -m uvicorn backend.app.main:app --reload --port 8000
```

Berhasil jika dokumentasi API dapat dibuka di
`http://localhost:8000/docs`.

### 2. Backend prototype - port 8009

```powershell
Set-Location prototypes/sampling-spec-rnd/backend
python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8009
```

Berhasil jika health check mengembalikan status sehat:

```powershell
Invoke-RestMethod http://localhost:8009/health
```

### 3. Frontend - port 3009

Pada terminal baru:

```powershell
Set-Location prototypes/sampling-spec-rnd/frontend
npm install
npm run dev
```

Berhasil jika halaman login terbuka di `http://localhost:3009`.

Frontend menggunakan proxy Vite: request `/api/v1` diteruskan ke backend port
8000, sedangkan request `/api` dan AI Copilot diteruskan ke backend port 8009.
Karena itu, jalankan ketiga service untuk mendapatkan fungsi aplikasi secara
lengkap.

## Kredensial Demo

- **Identifier:** `ADMIN-IT`
- **Password:** `Admin#12345`

Masukkan `ADMIN-IT` pada field login **identifier** di halaman
`http://localhost:3009`.

## Panduan Pengguna

Lihat [USER_GUIDE.md](./USER_GUIDE.md) untuk panduan lengkap penggunaan fitur
aplikasi.

## Catatan Proyek

Repository ini merupakan proyek hackathon **Kelompok 12 - MAIN Alkademi 2026**.
Folder `frontend/` di root repository adalah harness pengujian Playwright untuk
design mock, bukan aplikasi frontend utama. Aplikasi demo yang dijalankan adalah
`prototypes/sampling-spec-rnd/`.

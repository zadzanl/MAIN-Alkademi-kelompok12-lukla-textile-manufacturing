# 🚀 Panduan Setup & Menjalankan Prototype Sampling & Spec R&D

Dokumen ini menggabungkan seluruh instruksi setup, konfigurasi port, dan panduan operasional tim untuk modul prototype **Sampling & Spec R&D**.

---

## 📍 Lokasi Prototype dalam Repository
Modul prototype ini berada di:
- **Backend:** `prototypes/sampling-spec-rnd/backend` (FastAPI, Python 3.10+)
- **Frontend:** `prototypes/sampling-spec-rnd/frontend` (React 18, TypeScript, Vite, Tailwind CSS)

---

## ⚡ Langkah Tercepat (Quick Start)

### 1. Terminal 1 — Menjalankan Backend (Port 8009)
```bash
cd prototypes/sampling-spec-rnd/backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8009
```
*Atau di Windows cukup jalankan file batch:*
```cmd
prototypes\sampling-spec-rnd\backend\run_backend.bat
```

### 2. Terminal 2 — Menjalankan Frontend (Port 3009)
```bash
cd prototypes/sampling-spec-rnd/frontend
npm install
npm run dev
```
*Atau di Windows cukup jalankan file batch:*
```cmd
prototypes\sampling-spec-rnd\frontend\run_frontend.bat
```

---

## 🌐 Akses Layanan & Dokumentasi API

- **Frontend Application:** [http://localhost:3009](http://localhost:3009)
- **Backend API Interactive Docs (Swagger):** [http://localhost:8009/docs](http://localhost:8009/docs)
- **Backend ReDoc:** [http://localhost:8009/redoc](http://localhost:8009/redoc)
- **API Health Check:** [http://localhost:8009/api/sampling-spec-rnd/health](http://localhost:8009/api/sampling-spec-rnd/health)

---

## ⚙️ Konfigurasi Port & Integrasi (Port Alignment)

Sesuai standarisasi repository:
- **Backend Port:** `8009`
- **Frontend Port:** `3009`
- **Vite Proxy:** Frontend secara otomatis me-reverse proxy request `/api` ke `http://localhost:8009` tanpa kendala CORS.
- **CORS Backend:** Mengizinkan request dari `http://localhost:3009` dan `http://127.0.0.1:3009`.

---

## 🔧 Panduan Troubleshooting

### 1. Frontend tidak bisa terkoneksi ke Backend?
- Pastikan backend aktif di port 8009 (`uvicorn src.main:app --reload --port 8009`).
- Buka `http://localhost:8009/health` di browser untuk memastikan API aktif.
- Cek tab Console pada Browser DevTools (F12) untuk melihat error jaringan.

### 2. Port 8009 atau 3009 bentrok (sudah digunakan)?
- Cek proses yang menggunakan port di Windows PowerShell:
  ```powershell
  Get-NetTCPConnection -LocalPort 8009, 3009
  ```
- Matikan proses terkait jika diperlukan.

### 3. Masalah Dependency Python?
- Reinstall dependencies di virtual environment:
  ```bash
  pip install --upgrade --force-reinstall -r requirements.txt
  ```

---

## 💡 Fitur Utama Prototype
1. **Time Study Recording:** Pencatatan waktu siklus per unit dengan deteksi outlier dan status kalkulasi statistik.
2. **Specification Versioning:** Pelacakan histori perubahan parameter dan kalkulasi drift severity.
3. **Apple Design Interface:** Antarmuka tablet-ready dengan glassmorphism dan target sentuh 48px+.

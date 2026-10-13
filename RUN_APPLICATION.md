# 🚀 Cara Menjalankan Backend & Frontend

## Quick Start (3 Steps)

### Step 1: Clone Repository
```bash
git clone https://github.com/zadzanl/MAIN-Alkademi-hackathon-project1-amiga-textile.git
cd MAIN-Alkademi-hackathon-project1-amiga-textile
```

### Step 2: Start Backend (Terminal 1)
```bash
cd backend/sampling-spec-rnd
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8007
```

### Step 3: Start Frontend (Terminal 2)
```bash
cd frontend/sampling-spec-rnd
npm install
npm run dev
```

**Done! Akses aplikasi di:**
- Frontend: http://localhost:3007
- Backend Docs: http://127.0.0.1:8007/docs

---

## 📋 Detailed Instructions

### Prerequisites (Install Dulu)

**Windows:**
1. Python 3.8+ (dari python.org atau Windows Store)
2. Node.js 18+ (dari nodejs.org)
3. Git (dari git-scm.com)

**Verify instalasi:**
```bash
python --version
node --version
npm --version
git --version
```

---

## Backend Setup (Python FastAPI)

### Terminal 1 - Navigate to Backend

```bash
# Clone atau masuk ke folder project
cd MAIN-Alkademi-hackathon-project1-amiga-textile
cd backend/sampling-spec-rnd
```

### Create Virtual Environment

```bash
# Windows
python -m venv venv

# macOS/Linux
python3 -m venv venv
```

### Activate Virtual Environment

```bash
# Windows
.\venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

**Kalau sukses, prompt akan berubah menjadi:**
```
(venv) C:\...\backend\sampling-spec-rnd>
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

**Output yang diharapkan:**
```
Successfully installed fastapi uvicorn python-multipart
```

### Start Backend Server

```bash
uvicorn src.main:app --reload --port 8007
```

**Output yang diharapkan:**
```
INFO:     Uvicorn running on http://127.0.0.1:8007 (Press CTRL+C to quit)
INFO:     Started server process [12345]
INFO:     Application startup complete.
```

### Verify Backend Running

Buka browser, kunjungi:
```
http://127.0.0.1:8007/api/sampling-spec-rnd/health
```

**Expected Response:**
```json
{"status":"healthy","module":"sampling-spec-rnd"}
```

✅ Jika melihat response di atas, backend berhasil!

---

## Frontend Setup (React + TypeScript)

### Terminal 2 - Navigate to Frontend

```bash
# Buka terminal baru (jangan close backend)
cd MAIN-Alkademi-hackathon-project1-amiga-textile
cd frontend/sampling-spec-rnd
```

### Install Dependencies

```bash
npm install
```

**Ini akan menginstall semua package yang diperlukan.**

Output akan terlihat seperti:
```
npm notice
npm notice added 500+ packages in 45s
```

### Start Frontend Dev Server

```bash
npm run dev
```

**Output yang diharapkan:**
```
  VITE v4.5.14  ready in 1234 ms

  ➜  Local:   http://localhost:3007/
  ➜  Network: use --host to expose
  ➜  press h to show help
```

✅ Jika melihat ini, frontend berhasil!

---

## 🌐 Access Application

### Frontend UI
```
http://localhost:3007
```

**Yang akan terlihat:**
- Apple Design System interface
- Time Study page dengan glasmorphism effects
- Green checkmark: "🟢 Backend Connected"
- Input fields untuk membuat study baru

### Backend API Documentation
```
http://127.0.0.1:8007/docs
```

**Ini adalah Swagger UI untuk:**
- Lihat semua API endpoints
- Test endpoints langsung
- Lihat request/response format

### Backend Health Check
```
http://127.0.0.1:8007/api/sampling-spec-rnd/health
```

**Response:**
```json
{"status":"healthy","module":"sampling-spec-rnd"}
```

---

## 🧪 Testing Integration

### 1. Buka Frontend
```
http://localhost:3007
```

### 2. Verifikasi Backend Connected
- Lihat status: "🟢 Backend Connected" (warna hijau)
- Kalau merah/error, backend mungkin tidak running

### 3. Coba Buat Time Study
- Input nama proses di text field
- Klik tombol "Create Study"
- Lihat study muncul di list

### 4. Check Backend Logs
- Lihat terminal backend
- Harus ada log: `"POST /api/sampling-spec-rnd/studies/create HTTP/1.1" 200 OK`

✅ Jika semua di atas berhasil, integrasi frontend-backend working!

---

## 🛑 Stop Application

### Stop Backend (Terminal 1)
```bash
Press CTRL+C
```

### Stop Frontend (Terminal 2)
```bash
Press CTRL+C
```

---

## ⚠️ Troubleshooting

### Backend: Port 8007 Already in Use

**Error:**
```
Error: Address already in use
```

**Solution:**
```bash
# Cari process yang menggunakan port 8007
netstat -ano | findstr :8007

# Kill process (ganti 12345 dengan PID dari output di atas)
taskkill /PID 12345 /F
```

Atau gunakan port berbeda:
```bash
uvicorn src.main:app --reload --port 8008
```

### Frontend: Port 3007 Already in Use

**Error:**
```
error when starting dev server:
Error: listen EADDRINUSE: address already in use 0.0.0.0:3007
```

**Solution:**
Edit `frontend/sampling-spec-rnd/vite.config.ts`:
```typescript
server: {
  port: 3008,  // ubah ke port lain
  // ...
}
```

### Frontend Can't Connect to Backend

**Symptoms:**
- Red error message di frontend
- Can't create study

**Checklist:**
1. Backend running? Cek: `http://127.0.0.1:8007/api/sampling-spec-rnd/health`
2. Port 8007 sudah benar? Lihat: `vite.config.ts` proxy target
3. Check browser console: `F12` → Console tab → lihat error messages

### npm install Stuck

**Error:**
```
npm ERR! code ERESOLVE
npm ERR! ERESOLVE unable to resolve dependency tree
```

**Solution:**
```bash
npm install --legacy-peer-deps
```

### Python: ModuleNotFoundError

**Error:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Pastikan virtual environment aktif
.\venv\Scripts\activate

# Reinstall requirements
pip install -r requirements.txt
```

### Uvicorn: Command Not Found

**Error:**
```
'uvicorn' is not recognized as an internal or external command
```

**Solution:**
```bash
# Pastikan virtual environment aktif
.\venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

## 📝 File Structure untuk Reference

```
MAIN-Alkademi-hackathon-project1-amiga-textile/
│
├── backend/sampling-spec-rnd/
│   ├── venv/                          # Virtual environment (auto created)
│   ├── src/
│   │   ├── main.py                    # Entry point (FastAPI app)
│   │   ├── api/routes.py              # API endpoints
│   │   ├── models/                    # Data models
│   │   ├── services/                  # Business logic
│   │   └── utils/                     # Utilities
│   ├── requirements.txt               # Python dependencies
│   └── run_backend.bat                # Windows batch script
│
├── frontend/sampling-spec-rnd/
│   ├── node_modules/                  # Dependencies (auto created)
│   ├── src/
│   │   ├── main.tsx                   # React entry point
│   │   ├── pages/TimeStudyPage.tsx   # Main page
│   │   ├── components/                # React components
│   │   ├── services/api.ts            # API client
│   │   └── styles/                    # Design system & CSS
│   ├── package.json                   # NPM dependencies
│   ├── vite.config.ts                 # Vite config (includes API proxy)
│   └── run_frontend.bat               # Windows batch script
│
└── [Documentation files]
```

---

## 🔧 Environment Variables (Optional)

### Backend (.env)
Create `backend/sampling-spec-rnd/.env`:
```
DATABASE_URL=sqlite:///sampling_spec_rnd.db
API_PORT=8007
DEBUG=true
```

### Frontend (.env)
Create `frontend/sampling-spec-rnd/.env`:
```
VITE_API_URL=/api/sampling-spec-rnd
```

(Biasanya tidak perlu, defaults sudah benar)

---

## 🎯 URL Reference

| Purpose | URL |
|---------|-----|
| Frontend | http://localhost:3007 |
| Backend API | http://127.0.0.1:8007/api/sampling-spec-rnd |
| API Docs (Swagger) | http://127.0.0.1:8007/docs |
| API Docs (ReDoc) | http://127.0.0.1:8007/redoc |
| Health Check | http://127.0.0.1:8007/api/sampling-spec-rnd/health |
| OpenAPI Schema | http://127.0.0.1:8007/openapi.json |

---

## 💾 Batch Scripts (Windows Shortcut)

### Run Backend Quickly

Double-click `backend/sampling-spec-rnd/run_backend.bat`:
```batch
@echo off
call venv\Scripts\activate.bat
uvicorn src.main:app --reload --port 8007
pause
```

### Run Frontend Quickly

Double-click `frontend/sampling-spec-rnd/run_frontend.bat`:
```batch
@echo off
npm run dev
pause
```

---

## ✅ Success Checklist

- [ ] Python 3.8+ installed
- [ ] Node.js 18+ installed
- [ ] Git installed
- [ ] Repository cloned
- [ ] Backend virtual environment created
- [ ] Backend dependencies installed
- [ ] Backend server running (http://127.0.0.1:8007 responds)
- [ ] Frontend dependencies installed
- [ ] Frontend dev server running (http://localhost:3007)
- [ ] Frontend shows "🟢 Backend Connected"
- [ ] Can create time study from frontend
- [ ] Backend logs show API calls

---

## 📞 Quick Help

**Semua error?**
1. Cek semua prerequisites installed (`python --version`, `node --version`, `git --version`)
2. Baca error message di terminal dengan teliti
3. Try: `Ctrl+C` stop semua, close terminals, start fresh

**Backend tidak connect ke Frontend?**
1. Pastikan backend running: `http://127.0.0.1:8007/api/sampling-spec-rnd/health`
2. Pastikan frontend running: `http://localhost:3007`
3. Check browser console: `F12` → Console tab
4. Check browser network: `F12` → Network tab → lihat /api calls

---

## 🎉 Selesai!

Kalau semua langkah sudah selesai dan tidak ada error:

✅ **Backend dan Frontend sudah running!**

Buka browser:
- Frontend: http://localhost:3007
- API Docs: http://127.0.0.1:8007/docs

Mulai development! 🚀

---

**Last Updated**: October 13, 2026  
**Status**: Ready for team  
**Questions?**: Check TEAM_SETUP_GUIDE.md atau INTEGRATION_STATUS.md
